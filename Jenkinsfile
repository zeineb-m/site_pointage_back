pipeline {
    agent any

    options {
        skipDefaultCheckout()
    }

    tools {
        jdk 'JAVA_HOME'
        maven 'M2_HOME'
    }

    // environment {
    //     IMAGE_NAME = 'zeinebmaatalli/kaddem'               // Backend image
    //     FRONT_IMAGE = 'zeinebmaatalli/front-equipe'        // Frontend image
    //     DOCKER_USERNAME = 'zeinebmaatalli'
    //     DOCKER_PASSWORD = 'Zeineb123'
    //     COMPOSE_FILE = 'docker-compose.yml'
      
    // }

    stages {
        stage('1. Clone Repository') {
            steps {
                git branch: 'main', url: 'https://github.com/zeineb-m/site_pointage_back.git'
            }
        }

        stage('2. Check Maven Version') {
            steps {
                dir('zeinebmaatalli') {
                    sh 'mvn -version'
                }
            }
        }

        stage('3. Compile Project') {
            steps {
                dir('zeinebmaatalli') {
                    sh 'mvn clean compile'
                }
            }
        }

//         stage('4. Run Tests') {
//             steps {
//                 dir('zeinebmaatalli') {
//                     sh 'mvn test'
//                 }
//             }
//         }

//         stage('5. SonarQube Analysis') {
//             steps {
//                 dir('zeinebmaatalli-4TWIN1-G6') {
//                     sh '''
//                         mvn sonar:sonar \
//                         -Dsonar.login=squ_3cb2992aaa7ca0a4cbd9d35a29f52091ff332dfb
//                     '''
//                 }
//             }
//         }

//         stage('6. Package Application') {
//             steps {
//                 dir('zeinebmaatalli-4TWIN1-G6') {
//                     sh 'mvn package -DskipTests'
//                 }
//             }
//         }

//         stage('7. Deploy to Nexus') {
//             steps {
//                 dir('zeinebmaatalli-4TWIN1-G6') {
//                     sh 'mvn deploy -DskipTests'
//                 }
//             }
//         }

// stage('Build Backend Docker Image') {
//     steps {
//         dir('zeinebmaatalli-4TWIN1-G6') {
//             sh 'docker build -t $IMAGE_NAME .'
//         }
//     }
// }
//         stage('9. Build Frontend Docker Image') {
//             steps {
//                 sh 'docker build -t $FRONT_IMAGE -f equipe/dockerfile equipe'
//             }
//         }

//         stage('10. Push Docker Images to Docker Hub') {
//             steps {
//                 sh '''
//                     echo $DOCKER_PASSWORD | docker login -u $DOCKER_USERNAME --password-stdin
//                     docker push $IMAGE_NAME
//                     docker push $FRONT_IMAGE
//                 '''
//             }
//         }

//         stage('11. Restart Services with Docker Compose') {
//             steps {
//                 dir('zeinebmaatalli-4TWIN1-G6') {
//                     sh '''
//                         docker-compose -f $COMPOSE_FILE down || true
//                         docker-compose -f $COMPOSE_FILE up -d --build
//                     '''
//                 }
//             }
//         }
    }
}
