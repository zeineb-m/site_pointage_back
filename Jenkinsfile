pipeline {
    agent any

    options {
        skipDefaultCheckout()
    }

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

        stage('2. Check Maven Version') {
            steps {
                sh 'mvn -version'
            }
        }

        stage('3. Compile Project') {
            steps {
                sh 'mvn clean compile'
            }
        }
          stage('Check Files') {
    steps {
        sh 'ls -lah'
        sh 'find . -name "pom.xml"'
    }
}

    }
  
}
