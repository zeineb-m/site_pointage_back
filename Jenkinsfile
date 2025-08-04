pipeline {
    agent any

    tools {
        // Ces noms doivent correspondre à ceux configurés dans Jenkins > Manage Jenkins > Global Tool Configuration
        jdk 'JAVA_HOME'
        maven 'M2_HOME'
    }

    stages {
        stage('1. 🧬 Clone Repository') {
            steps {
                // Cloner explicitement la branche 'main'
                git branch: 'main', url: 'https://github.com/zeineb-m/site_pointage_back.git'
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

