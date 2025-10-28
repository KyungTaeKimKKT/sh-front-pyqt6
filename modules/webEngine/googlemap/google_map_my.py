from PyQt6 import QtCore, QtWidgets, QtWebEngineWidgets, QtWebChannel, QtNetwork
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from info import Info_SW as INFO

import json
import requests
import traceback
from modules.logging_config import get_plugin_logger


HTML = '''
<!doctype html>
<!--
 @license
 Copyright 2019 Google LLC. All Rights Reserved.
 SPDX-License-Identifier: Apache-2.0
-->
<html>
  <head>
    <title>Add Map</title>
    <style>
    /* Set the size of the div element that contains the map */
    #map {
        height: 100%; /* The height is 400 pixels */
        width: 100%; /* The width is the width of the web page */
        border : solid;
    }
    html, body {
        height: 100%;
        margin: 0;
        padding: 0;
    }
    </style>
    <link rel="stylesheet" type="text/css" href="./style.css" />
    <script type="module" src="./index.js"></script>
  </head>
  <body>
    <!--The div element for the map -->
    <div id="map"></div>

    <!-- prettier-ignore -->
    <script>(g=>{var h,a,k,p="The Google Maps JavaScript API",c="google",l="importLibrary",q="__ib__",m=document,b=window;b=b[c]||(b[c]={});var d=b.maps||(b.maps={}),r=new Set,e=new URLSearchParams,u=()=>h||(h=new Promise(async(f,n)=>{await (a=m.createElement("script"));e.set("libraries",[...r]+"");for(k in g)e.set(k.replace(/[A-Z]/g,t=>"_"+t[0].toLowerCase()),g[k]);e.set("callback",c+".maps."+q);a.src=`https://maps.${c}apis.com/maps/api/js?`+e;d[q]=f;a.onerror=()=>h=n(Error(p+" could not load."));a.nonce=m.querySelector("script[nonce]")?.nonce||"";m.head.append(a)}));d[l]?console.warn(p+" only loads once. Ignoring:",g):d[l]=(f,...n)=>r.add(f)&&u().then(()=>d[l](f,...n))})
        ({key: "API_KEY", v: "weekly"});</script>

    <script type="text/javascript">
            let mapElm = document.getElementById('map')
            
            // Initialize and add the map
            let map;

            async function initMap() {
            // The location of Uluru
            // const position =  { lat: 37.5503, lng: -122.0840897 };
            const position =  { lat: Number("LAT"), lng: Number("LNG") };
            // Request needed libraries.
            //@ts-ignore
            const { Map } = await google.maps.importLibrary("maps");
            const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");

            // The map, centered at Uluru
            map = new Map(document.getElementById("map"), {
                zoom: 13,
                center: position,
                mapId: "DEMO_MAP_ID",
            });

            // The marker, positioned at Uluru
            const marker = new AdvancedMarkerElement({
                map: map,
                position: position,
                title: "Uluru",
            });
            }

            initMap();

            // test용
            function gmap_return_test(data1, data2){
                return {
                    data1 : data1,
                    data2 : data2
                }
                return 'gmap_return_test'
            }

            // custom functions
            function gmap_addMarker_SearchPlace( latitude, longitude) {

                var coords = new google.maps.LatLng(latitude, longitude);
                // parameters['map'] = map;
                // parameters['position'] = coords;
                var marker = new google.maps.marker.AdvancedMarkerElement({
                    map,
                    position : coords,
                });
            }

            function gmap_setCenter(lat, lng) {
                map.setCenter(new google.maps.LatLng(lat, lng));
            }
            function gmap_getCenter() {
                return [map.getCenter().lat(), map.getCenter().lng()];
            }
            function gmap_setZoom(zoom) {
                map.setZoom(zoom);
            }
            function gmap_addMarker(key, latitude, longitude, parameters) {

                if (key in markers) {
                    gmap_deleteMarker(key);
                }
                var coords = new google.maps.LatLng(latitude, longitude);
                parameters['map'] = map
                parameters['position'] = coords;
                var marker = new google.maps.Marker(parameters);
                google.maps.event.addListener(marker, 'dragend', function () {
                    qtWidget.markerIsMoved(key, marker.position.lat(), marker.position.lng())
                });
                google.maps.event.addListener(marker, 'click', function () {
                    qtWidget.markerIsClicked(key, marker.position.lat(), marker.position.lng())
                });
                google.maps.event.addListener(marker, 'dblclick', function () {
                    qtWidget.markerIsDoubleClicked(key, marker.position.lat(), marker.position.lng())
                });
                google.maps.event.addListener(marker, 'rightclick', function () {
                    qtWidget.markerIsRightClicked(key, marker.position.lat(), marker.position.lng())
                });
                markers[key] = marker;
                return key;
            }
            function gmap_moveMarker(key, latitude, longitude) {
                var coords = new google.maps.LatLng(latitude, longitude);
                markers[key].setPosition(coords);
            }
            function gmap_deleteMarker(key) {
                markers[key].setMap(null);
                delete markers[key]
            }
            function gmap_changeMarker(key, extras) {
                if (!(key in markers)) {
                    return
                }
                markers[key].setOptions(extras);
            }

    </script>


  </body>
</html>
'''

JS = '''

'''

# JS = '''
# // main var
# // google map 관련해서
# let googleMapID='google-map-container';
# let googleMapElm = document.getElementById(googleMapID);
# let defaultCenter = { lat: 37.5519, lng: 126.9918 };
# let mapElm = googleMapElm.querySelector('#map');

# // main init function
# function initMap(parentElmID='google-map-container') {
#     let mapElm = googleMapElm.querySelector('#map');

#     const map = new google.maps.Map(mapElm, {
#         center: defaultCenter,
#         zoom: 13,
#         mapTypeControl: false,
#     });
#     const card = document.getElementById("pac-card");
#     const input = document.getElementById("pac-input");
#     const biasInputElement = document.getElementById("use-location-bias");
#     const strictBoundsInputElement = document.getElementById("use-strict-bounds");
#     const options = {
#         fields: ["formatted_address", "geometry", "name"],
#         strictBounds: false,
#     };
  
#     map.controls[google.maps.ControlPosition.TOP_LEFT].push(card);
  
#     window.autocomplete = new google.maps.places.Autocomplete(input, options);
#     // const autocomplete = new google.maps.places.Autocomplete(input, options);
  
#     // Bind the map's bounds (viewport) property to the autocomplete object,
#     // so that the autocomplete requests use the current map bounds for the
#     // bounds option in the request.
#     autocomplete.bindTo("bounds", map);
  
#     const infowindow = new google.maps.InfoWindow();
#     const infowindowContent = document.getElementById("infowindow-content");

#     infowindow.setContent(infowindowContent);
  
#     const marker = new google.maps.Marker({
#         map,
#         anchorPoint: new google.maps.Point(0, -29),
#     });
  
#     autocomplete.addListener("place_changed", () => {

#         infowindow.close();
#         marker.setVisible(false);

#         const place = autocomplete.getPlace();
#         console.log ( NOW() ,place )

#         if (!place.geometry || !place.geometry.location) {
#             // User entered the name of a Place that was not suggested and
#             // pressed the Enter key, or the Place Details request failed.                
#             // window.alert("No details available for input: '" + place.name + "'");
#             return;
#         }
    
#         // If the place has a geometry, then present it on a map.
#         if (place.geometry.viewport) {
#             map.fitBounds(place.geometry.viewport);
#         } else {
#             map.setCenter(place.geometry.location);
#             map.setZoom(17);
#         }
    
#         marker.setPosition(place.geometry.location);
#         marker.setVisible(true);

#         google.maps.event.addListener(marker, 'click', function(event) {
#             event.stop();

#             console.log( 'click');

#             clickElementArr.forEach( el => {
#             el.querySelector('.건물주소').textContent = place['formatted_address'];
#             el.querySelector('.loc_x').textContent = place.geometry.location.lat();
#             el.querySelector('.loc_y').textContent = place.geometry.location.lng();
#             })

#             setTimeout(function() {          
#                 if (confirm('database를 수정하시겠습니까?')) {
#                     clickElementArr.forEach ( el =>{
#                     let updateData = new Object();
#                     ['id','건물명','건물주소','loc_x','loc_y'].forEach( item =>{
#                         updateData[item] = el.querySelector(`.${item}`).textContent;
#                     })
#                     patchElevator(patchUrl+el.querySelector('.id').textContent+'/', updateData);
#                     })
#                 } else {
#                     alert('죄송합니다. database에 저장할 수 없읍니다.\n 다시 시도해주십시요');
#                 }
#                 location.reload();
#             }, 500);
#         });
#         infowindowContent.children["place-name"].textContent = place.name;
#         infowindowContent.children["place-address"].textContent = place.formatted_address;
#         infowindow.open(map, marker);




#     });
  
#     // Sets a listener on a radio button to change the filter type on Places
#     // Autocomplete.
#     function setupClickListener(id, types) {
#       const radioButton = document.getElementById(id);
  
#       radioButton.addEventListener("click", () => {
#         autocomplete.setTypes(types);
#         input.value = "";
#       });
#     }
  
#     setupClickListener("changetype-all", []);
#     setupClickListener("changetype-address", ["address"]);
#     setupClickListener("changetype-establishment", ["establishment"]);
#     setupClickListener("changetype-geocode", ["geocode"]);
#     setupClickListener("changetype-cities", ["(cities)"]);
#     setupClickListener("changetype-regions", ["(regions)"]);
#     biasInputElement.addEventListener("change", () => {
#       if (biasInputElement.checked) {
#         autocomplete.bindTo("bounds", map);
#       } else {
#         // User wants to turn off location bias, so three things need to happen:
#         // 1. Unbind from map
#         // 2. Reset the bounds to whole world
#         // 3. Uncheck the strict bounds checkbox UI (which also disables strict bounds)
#         autocomplete.unbind("bounds");
#         autocomplete.setBounds({ east: 180, west: -180, north: 90, south: -90 });
#         strictBoundsInputElement.checked = biasInputElement.checked;
#       }
  
#       input.value = "";
#     });
#     strictBoundsInputElement.addEventListener("change", () => {
#       autocomplete.setOptions({
#         strictBounds: strictBoundsInputElement.checked,
#       });
#       if (strictBoundsInputElement.checked) {
#         biasInputElement.checked = strictBoundsInputElement.checked;
#         autocomplete.bindTo("bounds", map);
#       }
  
#       input.value = "";
#     });
# }
# window.initMap = initMap;
# '''



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class GeoCoder(QtNetwork.QNetworkAccessManager):
    class NotFoundError(Exception):
        pass

    def geocode(self, location, api_key) ->tuple[float|None, float|None]:
        GOOGLE_JEOCODE_URL = f"https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={api_key}"

        response = requests.get( GOOGLE_JEOCODE_URL )

        if response.ok:
            return self._parseResult( response.json())
        else:
            return (None, None)
    
    def _parseResult( self, reply:dict) ->tuple[float|None, float|None]:
        results:dict = reply.get('results', [])
        try:
            if isinstance( results[0], dict ) and results[0]:
                result : dict = results[0]
                for key, value in result.items():
                    if key == 'geometry' : 
                        location:dict = value.get('location')
                        return (location.get('lat'), location.get('lng'))
            else:
                return (None, None)
        except:
            return (None, None)


    
    # def geocode(self, location, api_key):
        # url = QtCore.QUrl("https://maps.googleapis.com/maps/api/geocode/xml")

        # query = QtCore.QUrlQuery()
        # query.addQueryItem("key", api_key)
        # query.addQueryItem("address", location)
        # url.setQuery(query)

        # request = QtNetwork.QNetworkRequest(url)

        # reply = self.get(request)
        # loop = QtCore.QEventLoop()
        # reply.finished.connect(loop.quit)
        # loop.exec()
        # reply.deleteLater()
        # self.deleteLater()
        # return self._parseResult(reply)

    # def _parseResult(self, reply):
    #     xml = reply.readAll()
    #     reader = QtCore.QXmlStreamReader(xml)
    #     while not reader.atEnd():
    #         reader.readNext()
    #         if reader.name() != "geometry": continue
    #         reader.readNextStartElement()
    #         if reader.name() != "location": continue
    #         reader.readNextStartElement()
    #         if reader.name() != "lat": continue
    #         latitude = float(reader.readElementText())
    #         reader.readNextStartElement()
    #         if reader.name() != "lng": continue
    #         longitude = float(reader.readElementText())
    #         return latitude, longitude
    #     raise GeoCoder.NotFoundError


class QGoogleMap(QtWebEngineWidgets.QWebEngineView):
    signal_loadFinished = pyqtSignal(bool)

    mapMoved = QtCore.pyqtSignal(float, float)
    mapClicked = QtCore.pyqtSignal(float, float)
    mapRightClicked = QtCore.pyqtSignal(float, float)
    mapDoubleClicked = QtCore.pyqtSignal(float, float)

    markerMoved = QtCore.pyqtSignal(str, float, float)
    markerClicked = QtCore.pyqtSignal(str, float, float)
    markerDoubleClicked = QtCore.pyqtSignal(str, float, float)
    markerRightClicked = QtCore.pyqtSignal(str, float, float)

    def __init__(self, parent=None, api_key:str='', location:str=''):
        super(QGoogleMap, self).__init__(parent)
        self.defaultCords = (37.5503, 126.9971 )
        self._api_key = api_key if api_key else INFO.GOOGLE_MAP_API_KEY 
        channel = QtWebChannel.QWebChannel(self)
        self.page().setWebChannel(channel)
        channel.registerObject("qGoogleMap", self)
        # self.page().runJavaScript(JS)

        LAT, LNG = self.init_run(self._api_key, location)
        html = HTML.replace("API_KEY", self._api_key).replace('LAT', str( LAT )).replace('LNG', str( LNG ))
        self.setHtml(html)
        self.loadFinished.connect(self.on_loadFinished)
        self.initialized = False

        self._manager = QtNetwork.QNetworkAccessManager(self)
    
    def init_run(self,api_key:str='', location:str='') -> tuple[float, float]:
        try:
            if location:
                latitude, longitude = self.geocode(location)
            else:
                (latitude, longitude ) = self.defaultCords
        except:
            (latitude, longitude ) = self.defaultCords
        return  (latitude, longitude )

    def run(self, location:str='', zoom:int=13) -> None:
        """ center and mark"""
        self.centerAtAddress(location)
        self.addMarkerAtAddress(location)
        self.setZoom(zoom=14)

        #😀 test 용
        # data1 = 'abcdefg'
        # data2 = 'highklmnl'
        # self.page().runJavaScript(f"gmap_return_test('{data1}', '{data2}')", self.get_data_from_JS ) 

    def get_data_from_JS(self, data_from_JS:object):
        """ runJavaScript의 resultCallback 함수 """


    @QtCore.pyqtSlot()
    def on_loadFinished(self):
        self.initialized = True
        self.signal_loadFinished.emit( True )

  

    def waitUntilReady(self):
        if not self.initialized:
            loop = QtCore.QEventLoop()
            self.loadFinished.connect(loop.quit)
            loop.exec()

    def geocode(self, location):
        return GeoCoder(self).geocode(location, self._api_key)

    def centerAtAddress(self, location):
        try:
            latitude, longitude = self.geocode(location)

        except GeoCoder.NotFoundError:

            return None, None
        self.centerAt(latitude, longitude)
        return latitude, longitude

    def addMarkerAtAddress(self, location, **extra):
        if 'title' not in extra:
            extra['title'] = location
        try:
            latitude, longitude = self.geocode(location)
        except GeoCoder.NotFoundError:
            return None
        return self.addMarker(location, latitude, longitude, **extra)

    @QtCore.pyqtSlot(float, float)
    def mapIsMoved(self, lat, lng):
        self.mapMoved.emit(lat, lng)

    @QtCore.pyqtSlot(float, float)
    def mapIsClicked(self, lat, lng):
        self.mapClicked.emit(lat, lng)

    @QtCore.pyqtSlot(float, float)
    def mapIsRightClicked(self, lat, lng):
        self.mapRightClicked.emit(lat, lng)

    @QtCore.pyqtSlot(float, float)
    def mapIsDoubleClicked(self, lat, lng):
        self.mapDoubleClicked.emit(lat, lng)

    # markers
    @QtCore.pyqtSlot(str, float, float)
    def markerIsMoved(self, key, lat, lng):
        self.markerMoved.emit(key, lat, lng)

    @QtCore.pyqtSlot(str, float, float)
    def markerIsClicked(self, key, lat, lng):
        self.markerClicked.emit(key, lat, lng)

    @QtCore.pyqtSlot(str, float, float)
    def markerIsRightClicked(self, key, lat, lng):
        self.markerRightClicked.emit(key, lat, lng)

    @QtCore.pyqtSlot(str, float, float)
    def markerIsDoubleClicked(self, key, lat, lng):
        self.markerDoubleClicked.emit(key, lat, lng)

    def runScript(self, script, callback=None):
        if callback is None:
            self.page().runJavaScript(script)
        else:
            self.page().runJavaScript(script, callback)

    def centerAt(self, latitude, longitude):
        self.runScript("gmap_setCenter({},{})".format(latitude, longitude))

    def center(self):
        self._center = {}
        loop = QtCore.QEventLoop()

        def callback(*args):
            self._center = tuple(args[0])
            loop.quit()

        self.runScript("gmap_getCenter()", callback)
        loop.exec()
        return self._center

    def setZoom(self, zoom:int):
        self.runScript( f"gmap_setZoom({zoom})")

    def addMarker(self, key, latitude, longitude, **extra):
        # gmap_addMarker(key, latitude, longitude, parameters)

        self.runScript(f"gmap_addMarker_SearchPlace( {latitude},{longitude}  )")
        # self.runScript(f"gmap_addMarker({key},{latitude},{longitude}, {json.dumps(extra)})")
        # return self.runScript(
        #     "gmap_addMarker("
        #     "key={!r}, "
        #     "latitude={}, "
        #     "longitude={}, "
        #     "{}"
        #     "); ".format(key, latitude, longitude, json.dumps(extra)))

    def moveMarker(self, key, latitude, longitude):
        return self.runScript(
            "gmap_moveMarker({!r}, {}, {});".format(key, latitude, longitude))

    def setMarkerOptions(self, keys, **extra):
        return self.runScript(
            "gmap_changeMarker("
            "key={!r}, "
            "{}"
            "); "
                .format(keys, json.dumps(extra)))

    def deleteMarker(self, key):
        return self.runScript(
            "gmap_deleteMarker("
            "key={!r} "
            "); ".format(key))


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = QGoogleMap(api_key=INFO.GOOGLE_MAP_API_KEY)
    w.resize(640, 480)
    w.show()
    w.waitUntilReady()
    w.setZoom(14)
    # lat, lng = w.centerAtAddress("Lima Peru")
    # if lat is None and lng is None:
    #     lat, lng = -12.0463731, -77.042754
    #     w.centerAt(lat, lng)

    # w.addMarker("MyDragableMark", lat, lng, **dict(
    #     icon="http://maps.gstatic.com/mapfiles/ridefinder-images/mm_20_red.png",
    #     draggable=True,
    #     title="Move me!"
    # ))

    # for place in ["Plaza Ramon Castilla", "Plaza San Martin", ]:
    #     w.addMarkerAtAddress(place, icon="http://maps.gstatic.com/mapfiles/ridefinder-images/mm_20_gray.png")

    w.mapMoved.connect(print)
    w.mapClicked.connect(print)
    w.mapRightClicked.connect(print)
    w.mapDoubleClicked.connect(print)
    sys.exit(app.exec())
