import json
import pymongo
import time
import math

class Controller():
    def __init__(self):
        self.filtered_rstrts = list()
        self.cur_index = None
        self.cur_rstrt = None
        self.cur_coord = (0.0, 0.0)
        self.init_progress()

    def connect(self, ip, db_name):
        start = time.process_time()
        myclient = pymongo.MongoClient(host=ip,serverSelectionTimeoutMS=1000)
        print('connected',time.process_time()-start)
        if db_name not in myclient.list_database_names():
            mydb = myclient[db_name]
            mycol = mydb["restaurants"]
            mycol.create_index([("restaurant_id",pymongo.ASCENDING)],unique=True)
        
        self.mycol = myclient[db_name]["restaurants"]
        

    def add_rstrts_from_json(self, json_file):
        start = time.process_time()
        lines = self.read_json_file(json_file)
        print('read',time.process_time()-start)
        docs = list()
        for i, line in enumerate(lines):
            self.progress = (False, i/len(lines))
            data = json.loads(line)
            for grade in data["grades"]:
                # Give me a break :( If you dont +0.0, its type would be NumberLong. Dont ask me why
                grade["date"] = grade["date"]["$date"]+0.0
            docs.append(data)
            print(i)
        try:
            self.mycol.insert_many(docs,ordered=False)
        except Exception:
            pass
        self.close_progress()

    def read_json_file(self,json_file):
        lines = None
        with open( json_file) as f:
            lines = f.readlines()
        return lines
    
    def update_cur_rstrt(self, index):
        self.cur_index = None
        self.cur_rstrt = None
        if index is None:
            return
        self.cur_index = index
        rstrt_id = self.filtered_rstrts[index]['restaurant_id']
        res = self.mycol.find({'restaurant_id':rstrt_id})
        self.cur_rstrt = res[0]

    def update_rstrts(self, condition):
        start = time.process_time()
        query = dict()
        if condition.__contains__('name') and not condition['name'] == "":
            query['name'] =  { "$regex": "(.*)(%s)(.*)"%(condition['name']), '$options': "$i" }
        if condition.__contains__('borough') and not condition['borough'] == "":
            query['borough'] = { "$regex": "(.*)(%s)(.*)"%(condition['borough']), '$options': "$i" }
        if condition.__contains__('street') and not condition['street'] == "":
            query['address.street'] = { "$regex": "(.*)(%s)(.*)"%(condition['street']), '$options': "$i" }
        if condition.__contains__('zipcode') and not condition['zipcode'] == "":
            query['address.zipcode'] = { "$regex": "(.*)(%s)(.*)"%(condition['zipcode']), '$options': "$i" }
        self.filtered_rstrts = list(self.mycol.find(query,{
            "name": 1,
            "restaurant_id": 1,
            "address.coord": 1
        }))
        print('found',time.process_time()-start)
        for rstrt in self.filtered_rstrts:
            coord = rstrt['address']['coord']
            del rstrt['address']
            if coord and coord[0] and coord[1]:
                rstrt['dist'] = self.geodistance(coord[0],coord[1],self.cur_coord[0],self.cur_coord[1])
            else:
                rstrt['dist'] = 99999.99
        self.filtered_rstrts.sort(key=lambda r:r['dist'])

    
    def edit_info(self,docs):
        if self.cur_rstrt is None:
            return
        self.mycol.update_one({"restaurant_id": self.cur_rstrt["restaurant_id"]}, {'$set':docs} )
        self.cur_rstrt.update(docs)

    def edit_address(self,docs):
        if self.cur_rstrt is None:
            return
        docs.update({'coord':self.cur_rstrt['address']['coord']})
        docs = {'address':docs}
        self.mycol.update_one({"restaurant_id": self.cur_rstrt["restaurant_id"]}, {'$set':docs} )
        self.cur_rstrt.update(docs)

    def edit_coord(self,lng,lat):
        if self.cur_rstrt is None:
            return
        self.mycol.update_one(
            {"restaurant_id": self.cur_rstrt["restaurant_id"]},
            {'$set':{'address.coord':[lng,lat]}}
        )
        self.cur_rstrt['address']['coord'] = [lng,lat]
        for rstrt in self.filtered_rstrts:
            if rstrt["restaurant_id"] == self.cur_rstrt["restaurant_id"]:
                if lng and lat:
                    rstrt["dist"] = self.geodistance(lng,lat,self.cur_coord[0],self.cur_coord[1])
                else:
                    rstrt["dist"] = 99999.99
                return
        self.filtered_rstrts.sort(key=lambda r:r['dist'])
        
    def del_all(self):
        self.mycol.delete_many({"restaurant_id":{'$in':[rstrt["restaurant_id"] for rstrt in self.filtered_rstrts]}})
        self.filtered_rstrts = []
        self.cur_rstrt = None
    
    def del_rstrt(self):
        if self.cur_rstrt is not None:
            self.mycol.delete_one({"restaurant_id": self.cur_rstrt["restaurant_id"]})
            for index, rstrt in enumerate(self.filtered_rstrts):
                if rstrt["restaurant_id"] == self.cur_rstrt["restaurant_id"]:
                    del self.filtered_rstrts[index]
                    break
            self.cur_rstrt = None

    def new_rstrt(self):
        rstrts = self.filtered_rstrts
        new_r = dict(Controller.EMPTY_RSTRT)
        new_r['name'] = 'untitled'
        new_r['restaurant_id'] = str(int(self.get_max_id())+1)
        rstrts.insert(0,new_r)
        self.mycol.insert(new_r)

    def get_max_id(self):
        try:
            rstrt = self.mycol.find_one(sort=[('restaurant_id',-1)])
            return rstrt['restaurant_id']
        except Exception:
            return '100000000'

    def add_grade(self,grade,score):
        rstrt = self.cur_rstrt
        if rstrt is None:
            return
        tm = int(time.time()*1000)
        self.mycol.update_one({"restaurant_id":rstrt["restaurant_id"]},{"$push":{"grades":{
            'grade': grade,
            'score': score,
            'date': tm+0.0
        }}})
        rstrt["grades"].append({
            'grade': grade,
            'score': score,
            'date': tm
        })
    
    def del_grade(self,index):
        rstrt = self.cur_rstrt
        if rstrt is None:
            return
        rid = rstrt["restaurant_id"]
        # Waring: Not atomic operation
        # MongoDB still has defects
        self.mycol.update_one({"restaurant_id":rid}, {'$unset': {'grades.'+str(index):1}})
        self.mycol.update_one({"restaurant_id":rid}, {'$pull': {'grades':None}})
        del rstrt["grades"][index]

    def geodistance(self,lng1,lat1,lng2,lat2):
        lng1, lat1, lng2, lat2 = map(math.radians, [float(lng1), float(lat1), float(lng2), float(lat2)])
        # Longitude and latitude converted to radians
        dlon=lng2-lng1
        dlat=lat2-lat1
        a=math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        distance=2*math.asin(math.sqrt(a))*6371*1000 # Average radius of the earth，6371km
        distance=round(distance/1000,3)
        return distance
    
    def init_progress(self):
        self.progress = (False, 0)
    
    def close_progress(self):
        self.progress = (True, 1)

    EMPTY_RSTRT = {
        "address": {
            "building": "",
            "coord": [None, None],
            "street": "",
            "zipcode": ""
        },
        "borough": "",
        "cuisine": "",
        "grades": [],
        "name": "",
        "restaurant_id": ""
    }