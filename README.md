# CDC (Change Data Capture) with Debezium , Kafka , MySQL and Flask
## Requirement
 - The test Requires Docker in order to work 

Install docker
- docker-compose up -d

Add Connector to Debezium 
Windows CMD
- curl -X POST -H "Content-Type: application/json" -d "{\"name\":\"demo-mysql-connector\",\"config\":{\"connector.class\":\"io.debezium.connector.mysql.MySqlConnector\",\"database.hostname\":\"mysql_db\",\"database.port\":\"3306\",\"database.user\":\"demo\",\"database.password\":\"demo\",\"database.server.name\":\"demo_server\",\"database.include.list\":\"demo_db\",\"table.include.list\":\"demo_db.users\",\"database.server.id\":\"1234\",\"include.schema.changes\":\"true\",\"topic.prefix\":\"demo_server\",\"snapshot.mode\":\"initial\",\"schema.history.internal.kafka.bootstrap.servers\":\"kafka:9092\",\"schema.history.internal.kafka.topic\":\"schema-changes.demo_db\"}}" http://localhost:8083/connectors

Check if the Connection are Connected to the Debezium
- curl http://localhost:8083/connectors/demo-mysql-connector/status

Add Database and Table to MySQL
(Example Only)
- docker exec -it mysql_db mysql -u demo -pdemo -D demo_db -e "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(255), email VARCHAR(255));"
- docker exec -it mysql_db mysql -uroot -pmysql -e "GRANT SELECT, RELOAD, SHOW DATABASES, REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'demo'@'%'; FLUSH PRIVILEGES;"
- docker exec -it mysql_db mysql -u demo -pdemo -D demo_db -e "INSERT INTO users (id, name, email) VALUES (1, 'Alice', 'alice@example.com');"
- docker exec -it mysql_db mysql -u demo -pdemo -e "SHOW VARIABLES LIKE 'binlog_row_image';"


See using UI for CDC (Settings Included)
- http://localhost:9000/ (Kafdrop) to see if the topic is connected to Kafka
- http://localhost:8080/#app/ (Debezium UI) to see if Connector is properly installed or not
- http://localhost:5000/ (Flask) for Better UI for CDC Change rather than JSON File



This is simple example how to use Debezium and Kafka for Change Data Capture for Data
