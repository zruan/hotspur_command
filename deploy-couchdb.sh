HOST_DATA_PATH="/Users/gingerid/hotspur/couchdb/opt"
docker run -p 5984:5984 -v ${HOST_DATA_PATH}:/opt/couchdb/data -d --name hotspur_couchdb couchdb:latest