import os
import gmaps
import googlemaps
import argparse
import numpy as np
import json
import time

restaurant_loc = ['4 Điện Biên Phủ, Đa Kao, Quận 3, Hồ Chí Minh 700000, Vietnam', 
                  '32 Võ Văn Tần, Phường 6, Quận 3, Hồ Chí Minh, Vietnam', 
                  '10 Đặng Tất, Tân Định, Quận 1, Hồ Chí Minh, Vietnam',
                  '252 Điện Biên Phủ, Phường 7, Quận 3, Hồ Chí Minh 700000, Vietnam',
                  '2 Thi Sách, Bến Nghé, Quận 1, Hồ Chí Minh, Vietnam', 
                  '130 Nguyễn Trãi, Phường Phạm Ngũ Lão, Quận 1, Hồ Chí Minh 700000, Vietnam',
                  '21 Hàn Thuyên, Bến Nghé, Quận 1, Hồ Chí Minh, Vietnam',
                  '21 Hoàng Việt, Phường 4, Tân Bình, Hồ Chí Minh 700000, Vietnam']
time_window = [(0, 10000),
              (0, 3000),
              (0, 3000),
              (0, 5000),
              (0, 8000),
              (0, 9000),
              (0, 7000),
              (0, 10000),]
depot = 0


gmaps.configure(api_key='AIzaSyAQWqMTOcyLBRDR2skO4F_5QEWzNDOlUHw')
GOOGLE_API = googlemaps.Client(key='AIzaSyAQWqMTOcyLBRDR2skO4F_5QEWzNDOlUHw')
GOOGLE_API

# Save data into json
json_data = {}
json_data['destination'] = []
for rest in restaurant_loc:
    geocode_res = GOOGLE_API.geocode(rest)
    json_data['destination'].append(geocode_res[0])
json_data['time_window'] = time_window
json_data['depot'] = depot
json.dump(json_data, open('./sample/tsptw.json', 'w'))
