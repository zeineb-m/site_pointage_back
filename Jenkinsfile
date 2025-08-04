pipeline {
    agent any

    tools {
        // Assurez-vous que ces noms correspondent à ceux configurés dans Jenkins > Manage Jenkins > Global Tool Configuration
        jdk 'JAVA_HOME'
        maven 'M2_HOME'
    }

    stages {
        stage('1. 🧬 Clone Repository') {
            steps {
                // Jenkins fait déjà un checkout par défaut, mais ici tu forces le checkout de ta branche
                git branch: 'main', url: 'https://github.com/zeineb-m/site_pointage_back.git'
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
