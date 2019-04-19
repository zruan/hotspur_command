HOST_DATA_PATH="/pncc/storage/1/processing/hotspur/couchdb"
docker run -p 5984:5984 -v ${HOST_DATA_PATH}:/opt/couchdb/data -d --name hotspur_couchdb couchdb:latest
