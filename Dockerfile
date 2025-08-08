FROM openjdk:17
EXPOSE 8081
ADD http://127.0.0.1:8081/repository/maven-releases/com/example/stage/0.0.1/stage-0.0.1.jar stage-0.0.1.jar
ENTRYPOINT ["java","-jar","/stage-0.0.1-SNAPSHOT.jar"]
