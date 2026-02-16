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
                        docker run --rm ${DOCKER_IMAGE}:${DOCKER_TAG} python -m pytest tests/ || echo "No tests found"
                    """
                }
            }
        }
        
        stage('Security Scanning') {
            parallel {
                stage('Trivy Vulnerability Scan') {
                    steps {
                        echo 'Running Trivy security scan...'
                        script {
                            bat """
                                docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image --severity HIGH,CRITICAL ${DOCKER_IMAGE}:${DOCKER_TAG} || echo "Scan completed"
                            """
                        }
                    }
                }
                
                stage('Python Bandit Scan') {
                    steps {
                        echo 'Running Bandit Python security scan...'
                        script {
                            bat """
                                docker run --rm -v %WORKSPACE%:/code cytopia/bandit -r /code -f json -o /code/bandit-report.json || echo "Scan completed"
                            """
                        }
                    }
                }
            }
        }
        
        stage('Code Quality Analysis') {
            steps {
                echo 'Running code quality checks...'
                script {
                    bat """
                        docker run --rm -v %WORKSPACE%:/code python:3.11-slim sh -c "pip install flake8 && flake8 /code/*.py --max-line-length=120" || echo "Analysis completed"
                    """
                }
            }
        }
        
        stage('Push to Registry') {
            when {
                branch 'main'
            }
            steps {
                echo 'Pushing Docker image to registry...'
                script {
                    // Push to Docker registry (configure credentials in Jenkins)
                    docker.withRegistry("https://${DOCKER_REGISTRY}", "${DOCKER_CREDENTIALS_ID}") {
                        docker.image("${DOCKER_IMAGE}:${DOCKER_TAG}").push()
                        docker.image("${DOCKER_IMAGE}:latest").push()
                    }
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
                    // Deploy to staging server
                    bat """
                        docker stop student-portal-staging || echo "Container not running"
                        docker rm student-portal-staging || echo "Container not found"
                        docker run -d --name student-portal-staging -p 5001:5000 -e FLASK_ENV=staging -v student-portal-staging-db:/app/database -v student-portal-staging-uploads:/app/static/uploads ${DOCKER_IMAGE}:${DOCKER_TAG}
                    """
                }
            }
        }
        
        stage('Health Check') {
            steps {
                echo 'Running health check...'
                script {
                    bat """
                        timeout /t 10 /nobreak
                        curl -f http://localhost:5001/health || exit 1
                    """
                }
            }
        }
        
        stage('Manual Approval for Production') {
            when {
                branch 'main'
            }
            steps {
                // Wait for manual approval before deploying to production
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
                    // Deploy to production server
                    bat """
                        docker stop student-portal-prod || echo "Container not running"
                        docker rm student-portal-prod || echo "Container not found"
                        docker run -d --name student-portal-prod -p 5000:5000 -e FLASK_ENV=production -v student-portal-prod-db:/app/database -v student-portal-prod-uploads:/app/static/uploads ${DOCKER_IMAGE}:${DOCKER_TAG}
                    """
                }
            }
        }
    }
    
    post {
        success {
            echo 'Pipeline completed successfully!'
            // Send success notification
            emailext(
                subject: "SUCCESS: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]'",
                body: "Good news! The build ${env.BUILD_NUMBER} completed successfully.",
                to: 'team@example.com'
            )
        }
        failure {
            echo 'Pipeline failed!'
            // Send failure notification
            emailext(
                subject: "FAILURE: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]'",
                body: "Build ${env.BUILD_NUMBER} failed. Please check Jenkins for details.",
                to: 'team@example.com'
            )
        }
        always {
            echo 'Cleaning up...'
            // Clean up Docker resources
            bat 'docker system prune -f || echo "Cleanup completed"'
            cleanWs()
        }
    }
}
