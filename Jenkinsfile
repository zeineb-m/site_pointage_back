pipeline {
    agent any

    tools {
        jdk 'JAVA_HOME'
        maven 'M2_HOME'
    }

    environment {
        IMAGE_NAME = 'zeinebmaatalli/stage'
        DOCKER_USERNAME = 'zeinebmaatalli'
        DOCKER_PASSWORD = 'Zeineb123'
    }

    stages {
        stage('1. Clone Repository') {
            steps {
                git branch: 'main', url: 'https://github.com/zeineb-m/site_pointage_back.git'
            }
        }

        stage('2. Build avec Maven') {
            steps {
                sh 'mvn clean install'
            }
        }

        stage('3. Run Tests') {
            steps {
                sh 'mvn test'
            }
        }

//         stage('4. Analyse SonarQube') {
//             steps {
//                 sh 'mvn sonar:sonar -Dsonar.login=e5aa2062191baf81e375649795ee4b8c0351ecb9 -Dsonar.projectKey=site_pointage_back -Dsonar.host.url=http://localhost:9000'
//             }
//         }
//
//         stage('5. Deploy to Nexus') {
//             steps {
//                 sh 'mvn deploy -DskipTests'
//             }
//         }

        stage('6. Build Backend Docker Image') {
            steps {
                sh "docker build -t ${IMAGE_NAME} ."
            }
        }

        stage('7. Docker Login & Push Image') {
            steps {
                sh '''
                    echo $DOCKER_PASSWORD | docker login -u $DOCKER_USERNAME --password-stdin
                    docker push $IMAGE_NAME
                '''
            }
        }

       stage('8. Restart Services with Docker Compose') {
    steps {
        dir("${WORKSPACE}") {
            sh '''
                docker compose down || true
                docker compose up -d --build
            '''
        }
    }
}

    post {
        success {
            echo '🎉 Build succeeded!'
        }
        failure {
            echo '❌ Build failed. Please check logs.'
        }
    }
}
