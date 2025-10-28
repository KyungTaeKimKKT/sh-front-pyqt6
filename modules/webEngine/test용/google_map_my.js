function initMap(parentElmID='google-map-container') {
    let mapElm = googleMapElm.querySelector('#map');

    const map = new google.maps.Map(mapElm, {
        center: defaultCenter,
        zoom: 13,
        mapTypeControl: false,
    });
    const card = document.getElementById("pac-card");
    const input = document.getElementById("pac-input");
    const biasInputElement = document.getElementById("use-location-bias");
    const strictBoundsInputElement = document.getElementById("use-strict-bounds");
    const options = {
        fields: ["formatted_address", "geometry", "name"],
        strictBounds: false,
    };
  
    map.controls[google.maps.ControlPosition.TOP_LEFT].push(card);
  
    window.autocomplete = new google.maps.places.Autocomplete(input, options);
    // const autocomplete = new google.maps.places.Autocomplete(input, options);
  
    // Bind the map's bounds (viewport) property to the autocomplete object,
    // so that the autocomplete requests use the current map bounds for the
    // bounds option in the request.
    autocomplete.bindTo("bounds", map);
  
    const infowindow = new google.maps.InfoWindow();
    const infowindowContent = document.getElementById("infowindow-content");

    infowindow.setContent(infowindowContent);
  
    const marker = new google.maps.Marker({
        map,
        anchorPoint: new google.maps.Point(0, -29),
    });
  
    autocomplete.addListener("place_changed", () => {

        infowindow.close();
        marker.setVisible(false);

        const place = autocomplete.getPlace();
        console.log ( NOW() ,place )

        if (!place.geometry || !place.geometry.location) {
            // User entered the name of a Place that was not suggested and
            // pressed the Enter key, or the Place Details request failed.                
            // window.alert("No details available for input: '" + place.name + "'");
            return;
        }
    
        // If the place has a geometry, then present it on a map.
        if (place.geometry.viewport) {
            map.fitBounds(place.geometry.viewport);
        } else {
            map.setCenter(place.geometry.location);
            map.setZoom(17);
        }
    
        marker.setPosition(place.geometry.location);
        marker.setVisible(true);

        google.maps.event.addListener(marker, 'click', function(event) {
            event.stop();

            console.log( 'click');

            clickElementArr.forEach( el => {
            el.querySelector('.건물주소').textContent = place['formatted_address'];
            el.querySelector('.loc_x').textContent = place.geometry.location.lat();
            el.querySelector('.loc_y').textContent = place.geometry.location.lng();
            })

            setTimeout(function() {          
                if (confirm('database를 수정하시겠습니까?')) {
                    clickElementArr.forEach ( el =>{
                    let updateData = new Object();
                    ['id','건물명','건물주소','loc_x','loc_y'].forEach( item =>{
                        updateData[item] = el.querySelector(`.${item}`).textContent;
                    })
                    patchElevator(patchUrl+el.querySelector('.id').textContent+'/', updateData);
                    })
                } else {
                    alert('죄송합니다. database에 저장할 수 없습니다.\n 다시 시도해주십시요');
                }
                location.reload();
            }, 500);
        });
        infowindowContent.children["place-name"].textContent = place.name;
        infowindowContent.children["place-address"].textContent = place.formatted_address;
        infowindow.open(map, marker);




    });
  
    // Sets a listener on a radio button to change the filter type on Places
    // Autocomplete.
    function setupClickListener(id, types) {
      const radioButton = document.getElementById(id);
  
      radioButton.addEventListener("click", () => {
        autocomplete.setTypes(types);
        input.value = "";
      });
    }
  
    setupClickListener("changetype-all", []);
    setupClickListener("changetype-address", ["address"]);
    setupClickListener("changetype-establishment", ["establishment"]);
    setupClickListener("changetype-geocode", ["geocode"]);
    setupClickListener("changetype-cities", ["(cities)"]);
    setupClickListener("changetype-regions", ["(regions)"]);
    biasInputElement.addEventListener("change", () => {
      if (biasInputElement.checked) {
        autocomplete.bindTo("bounds", map);
      } else {
        // User wants to turn off location bias, so three things need to happen:
        // 1. Unbind from map
        // 2. Reset the bounds to whole world
        // 3. Uncheck the strict bounds checkbox UI (which also disables strict bounds)
        autocomplete.unbind("bounds");
        autocomplete.setBounds({ east: 180, west: -180, north: 90, south: -90 });
        strictBoundsInputElement.checked = biasInputElement.checked;
      }
  
      input.value = "";
    });
    strictBoundsInputElement.addEventListener("change", () => {
      autocomplete.setOptions({
        strictBounds: strictBoundsInputElement.checked,
      });
      if (strictBoundsInputElement.checked) {
        biasInputElement.checked = strictBoundsInputElement.checked;
        autocomplete.bindTo("bounds", map);
      }
  
      input.value = "";
    });
}