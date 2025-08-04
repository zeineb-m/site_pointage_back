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
    }
 stage('Compile') {
            steps {
                sh 'mvn clean compile'
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

