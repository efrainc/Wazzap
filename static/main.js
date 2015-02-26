function initialize() {

  var mapOptions = {
    mapTypeId: google.maps.MapTypeId.ROADMAP,
    streetViewControl: false,
    mapTypeControl: false,
    center: { lat: 47.645101, lng: 237.658112},
    zoom: 13
  };

  var map = new google.maps.Map(document.getElementById('map-canvas'), mapOptions);

  map.data.loadGeoJson("/static/venue.json");

  map.data.setStyle({
    icon: '/static/hifi.png',
    fillColor: 'green'
  });

  // Create icons
  // var iconURL = 'https://s3-us-west-2.amazonaws.com/wassap/hifi.png';
  // var iconSize = new google.maps.Size(34 ,34);
  // var iconOrigin = new google.maps.Point(0,0);
  // var iconAnchor = new google.maps.Point(10,34);
  // var myIcon = {
  //   url: iconURL,
  //   size: iconSize, 
  //   origin: iconOrigin,
  //   anchor: iconAnchor
  // };


  // Create a marker for each place using icons
  // var marker = new google.maps.Marker({
  //   map: map,
  //   icon: myIcon,
  //   title: 'test',
  //   position: new google.maps.LatLng(47.650101, 237.65112)
  // });


  var styles = [
    {
      "featureType": "water",
      "stylers": [
        { "hue": "#0044ff" },
        { "lightness": -17 }
      ]
    },{
      "featureType": "poi.park",
      "stylers": [
        { "hue": "#3bff00" },
        { "lightness": -18 }
      ]
    },{
      featureType: "road",
      elementType: "geometry",
      stylers: [
        { lightness: 100 },
        { visibility: "simplified" }
      ]
    },{
      featureType: "road",
      elementType: "labels",
      stylers: [
        { visibility: "off" }
      ]
    }
  ];

  map.setOptions({styles: styles});

  var markers = [];


  // Create the search box and link it to the UI element.
  var input = /** @type {HTMLInputElement} */(
  document.getElementById('pac-input'));

  map.controls[google.maps.ControlPosition.TOP_LEFT].push(input);

  var searchBox = new google.maps.places.SearchBox((input));

// Listen for the event fired when the user selects an item from the
// pick list. Retrieve the matching places for that item.
google.maps.event.addListener(searchBox, 'places_changed', function() {
  var places = searchBox.getPlaces();

  // var geojson = JSON.parse(places);
  // map.data.addGeoJson(places);
  // var featurized = Data.Feature(places[0]);
  // map.data.add(places[0].geometry);
  var feature = map.data.add(places[0].geometry);
  map.data.setMap(map);


  $.ajax({
      url: '/writelocation',
      type: 'POST',
      dataType: 'json',
      data: {'venue': places[0].name,'address': places[0].formatted_address},
      success: function(result){
        // get lat long from address
        // create a new pin
      }
    })

  map.panTo(places[0].geometry.location);

  });
  // if (places.length == 0) {
  // return;
  // }
  // for (var i = 0, marker; marker = markers[i]; i++) {
  // marker.setMap(null);
  // }

  // // For each place, get the icon, place name, and location.
  // markers = [];
  // var bounds = new google.maps.LatLngBounds();
  // for (var i = 0, place; place = places[i]; i++) {
  // var image = {
  //   url: place.icon,
  //   size: new google.maps.Size(71, 71),
  //   origin: new google.maps.Point(0, 0),
  //   anchor: new google.maps.Point(17, 34),
  //   scaledSize: new google.maps.Size(25, 25)
  // };

  // // Create a marker for each place.
  // var marker = new google.maps.Marker({
  //   map: map,
  //   icon: image,
  //   title: place.name,
  //   position: place.geometry.location
  // });

  // marker.setMap(null)
  // markers.push(marker);

  // bounds.extend(place.geometry.location);
  // }
  // map.fitBounds(bounds);

  // Bias the SearchBox results towards places that are within the bounds of the
  // current map's viewport.
  google.maps.event.addListener(map, 'bounds_changed', function() {
  var bounds = map.getBounds();
  searchBox.setBounds(bounds);
  });


  map.data.addListener('click', function(event) {
    var address = event.feature["k"]["address"].slice(0, -5);

    $.ajax({
        url: '/gettweets',
        type: 'GET',
        dataType: 'json',
        data: {'address': address},
        success: function(result){
          $('#sidebar').html("");
          var venue_name = Mustache.to_html('<h2>{{venue}}</h2>', result);
          $('#sidebar').append(venue_name);
          var template = '<div class="tweet">'+
                            '<span class="user">{{author_handle}}</span>'+
                            '<span class="time">{{time}}</span>'+
                            '<p class="content">{{{content}}}'+
                          '</div>';

          var tweets = result.tweets;
          for(var tweet in tweets){
            tweet_content = tweets[tweet].content.split(" ");
            for (var word in tweet_content){
              if (tweet_content[word][0] == '@'){
                tweet_content[word] = tweet_content[word].replace(":","");
                tweet_content[word] = "<a href='https://twitter.com/"+ tweet_content[word].substring(1) + "'>"+tweet_content[word]+"</a>";
              }
              else if (tweet_content[word].substring(0, 4) == 'http'){
                tweet_content[word] = "<a href='" + tweet_content[word] + "'>"+tweet_content[word]+"</a>";
              }
            }
            tweets[tweet].content = tweet_content.join(" ");

            var html = Mustache.to_html(template, tweets[tweet]);
            $('#sidebar').append(html);
          }
        },
    });

    $('#sidebar').addClass("sidebar--active");
  });
}
// Load geojson data
google.maps.event.addDomListener(window, 'load', initialize);