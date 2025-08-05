pipeline {
    agent any

    tools {
        jdk 'JAVA_HOME'
        maven 'M2_HOME'
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

        stage('3. Package JAR') {
            steps {
                sh 'mvn package -DskipTests'
            }
        }

        stage('4. Run Tests') {
            steps {
                sh 'mvn test'
            }
        }

        stage('5. Analyse SonarQube') {
            steps {
                sh 'mvn sonar:sonar -Dsonar.login=5c3dfe9177dcc6c925adb6e26f91c4b0506d9ccd -Dsonar.projectKey=site_pointage_back -Dsonar.host.url=http://localhost:9000'
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
