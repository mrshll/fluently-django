console.log("including video");

function sessionConnectHandler (event) {
  subscribeToStreams(event.streams);
  var div = document.createElement('div');
  div.setAttribute('id', 'publisher');

  var publisherContainer = document.getElementById('video_small');
  // This example assumes that a publisherContainer div exists
  publisherContainer.appendChild(div);

  var publisherProperties = {width: '100%', height:'100%', name:"local stream"};
  publisher = TB.initPublisher(apiKey, 'publisher', publisherProperties);

  session.publish(publisher);
}

function subscribeToStreams(streams) {
  for (i = 0; i < streams.length; i++) {
    var stream = streams[i];
    if (stream.connection.connectionId != session.connection.connectionId) {
      displayStream(stream);
    }
  }
}

function displayStream(stream) {
  var div = document.createElement('div');
  div.setAttribute('id', 'stream' + stream.streamId);
  var streamsContainer = document.getElementById('video');
  streamsContainer.appendChild(div);
  subscriber = session.subscribe(stream, 'stream' + stream.streamId);
  $('#stream'+stream.streamId).width('100%');
  $('#stream'+stream.streamId).height('100%');
  console.log("added a stream");
}

function streamCreatedHandler(event) {
  console.log("stream created");
  subscribeToStreams(event.streams);
}

var session = TB.initSession(session_id);
session.addEventListener("sessionConnected", sessionConnectHandler);
session.addEventListener("streamCreated", streamCreatedHandler);
session.connect(apiKey, tok_token);


