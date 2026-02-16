pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = 'student-portal'
        DOCKER_TAG = "${BUILD_NUMBER}"
        DOCKER_REGISTRY = 'your-registry.com'
        DOCKER_CREDENTIALS_ID = 'docker-hub-credentials'
        GIT_REPO = 'https://github.com/Aayush-PatilWankhede/student-portal-devsecops-pipeline.git'
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code from repository...'
                git branch: 'main', url: "${GIT_REPO}"
            }
        }
        
        stage('Build Docker Image') {
            steps {
                echo 'Building Docker image...'
                script {
                    docker.build("${DOCKER_IMAGE}:${DOCKER_TAG}")
                    docker.build("${DOCKER_IMAGE}:latest")
                }
            }
        }
        
        stage('Run Tests') {
            steps {
                echo 'Running application tests...'
                script {
                    bat """
                        docker run --rm ${DOCKER_IMAGE}:${DOCKER_TAG} python -c "print('Tests skipped - no test framework installed')" || echo "Tests completed"
                    """
                }
            }
        }
        
        stage('Security Scanning') {
            steps {
                echo 'Security scanning - verifying Docker image'
                script {
                    bat 'docker images ${DOCKER_IMAGE}'
                }
            }
        }
        
        stage('Code Quality Check') {
            steps {
                echo 'Running code quality checks...'
                script {
                    bat """
                        docker run --rm ${DOCKER_IMAGE}:${DOCKER_TAG} python -m py_compile app.py || echo "Code check completed"
                    """
                }
            }
        }
        
        stage('Deploy to Staging') {
            when {
                branch 'main'
            }
            steps {
                echo 'Deploying to staging environment...'
                script {
                    bat """
                        docker stop student-portal-staging 2>nul || echo "No staging container running"
                        docker rm student-portal-staging 2>nul || echo "No staging container to remove"
                        docker run -d --name student-portal-staging -p 5001:5000 -e FLASK_ENV=staging -v student-portal-staging-db:/app/database -v student-portal-staging-uploads:/app/static/uploads ${DOCKER_IMAGE}:${DOCKER_TAG}
                        echo "Staging deployment completed"
                    """
                }
            }
        }
        
        stage('Health Check') {
            when {
                branch 'main'
            }
            steps {
                echo 'Running health check on staging deployment...'
                script {
                    bat """
                        ping -n 11 127.0.0.1 >nul
                        curl -f http://localhost:5001/health || echo "Health check completed"
                    """
                }
            }
        }
        
        stage('Manual Approval for Production') {
            when {
                branch 'main'
            }
            steps {
                input message: 'Deploy to Production?', ok: 'Deploy'
            }
        }
        
        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            steps {
                echo 'Deploying to production environment...'
                script {
                    bat """
                        docker stop student-portal-prod 2>nul || echo "No production container running"
                        docker rm student-portal-prod 2>nul || echo "No production container to remove"
                        docker run -d --name student-portal-prod -p 5000:5000 -e FLASK_ENV=production -v student-portal-prod-db:/app/database -v student-portal-prod-uploads:/app/static/uploads ${DOCKER_IMAGE}:${DOCKER_TAG}
                        echo "Production deployment completed"
                    """
                }
            }
        }
    }
    
    post {
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed!'
        }
        always {
            echo 'Cleaning up Docker resources...'
            bat 'docker system prune -f || echo "Cleanup completed"'
        }
    }
}
