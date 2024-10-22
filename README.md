# Telco LLM

## Setup Weaviate as a Knowledge Base
```bash
docker network create weaviate-net
docker run -d --name weaviate --network weaviate-net -p 8080:8080 -p 50051:50051 cr.weaviate.io/semitechnologies/weaviate:1.27.0
docker run -d --name weaviate-playground -p 3000:80 semitechnologies/weaviate-playground:latest
```

## Check Weaviate data
Visit: http://${SERVICE_HOST}:3000/?weaviate_uri=http%3A%2F%2F${SERVICE_HOST}%3A8080%2Fv1%2Fgraphql&graphiql

Run the following GraphQL query:
```bash
{
  Get {
    Alarm {
      _additional {
        id  # Get the unique ID of each instance
      }
      content   # Assuming 'text' is the property for alarm messages
      len       # Metadata property for the length of each message
      remedy    # Metadata property for the remedy information
    }
  }
}

```

## Build and Run using Docker
```bash
docker build -t telco_llm .
docker run  --rm --name telco --network weaviate-net -p 5000:5000 -e FIREWORKS_API_KEY=xxxxxxxxx telco_llm:latest
```

## API Document
+ https://${SERVICE_HOST}/docs

## Health Check
```bash
curl --location 'https://${SERVICE_HOST}/blueprint/healthz'
```

## Sample Request
```bash
curl --location 'https://${SERVICE_HOST}/recommendation' \
--header 'Content-Type: application/json' \
--data '{
  "customer_id": "42",
  "order_time": "2023-05-07T18:00:58",
  "customer_latitude": 35.763358,
  "customer_longitude": 51.411085
}'
```
```bash
curl --location 'https://${SERVICE_HOST}/travel-time' \
--header 'Content-Type: application/json' \
--data '{
    "source_latitude": 35.763358,
    "source_longitude": 51.411085,
    "destination_latitude": 35.773358,
    "destination_longitude": 51.311085
}'
```


## Run on local system without Docker
```bash
git clone https://github.com/xei/fastapi-blueprint.git
cd astapi-blueprint
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
PYTHONPATH=PATH/TO/PROJ/app uvicorn main:app --reload
```

## Run on local system with Docker
```
docker run $CONTAINER_REGISTRY_PATH/blueprint:latest
```

## Deploy new changes (It is automated in Gitlab CI)
```bash
docker pull $CONTAINER_REGISTRY_PATH/blueprint:latest || true
docker build --cache-from $CONTAINER_REGISTRY_PATH/blueprint:latest -f Dockerfile -t $CONTAINER_REGISTRY_PATH/blueprint:latest .
docker push $CONTAINER_REGISTRY_PATH/blueprint:latest:latest
docker stack deploy -c docker-compose.yml --with-registry-auth blueprint
```
