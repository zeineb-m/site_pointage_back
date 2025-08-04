pipeline {
    agent any

    tools {
        jdk 'JAVA_HOME'
        maven 'M2_HOME'
    }

    stages {
        stage('1. 🧬 Clone Repository') {
            steps {
                git branch: 'main', url: 'https://github.com/zeineb-m/site_pointage_back.git'
            }
        }

        stage('2. ⚙️ Build avec Maven') {
            steps {
                sh 'mvn clean install'
            }
        }

        stage('3. ✅ Tests unitaires') {
            steps {
                sh 'mvn test'
            }
        }
    }

     stage('Package JAR') {
            steps {
                sh 'mvn package -DskipTests'
            }
        }

        stage('MVN SONARQUBE') {
            steps {
                sh "mvn sonar:sonar -Dsonar.login=squ_a546fefc5f50e9f80714f82c88e69e723519390a -Dmaven.test.skip=true"
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


