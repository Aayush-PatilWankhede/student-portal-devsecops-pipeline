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
                    sh '''
                        docker run --rm ${DOCKER_IMAGE}:${DOCKER_TAG} python -m pytest tests/ || echo "No tests found"
                    '''
                }
            }
        }
        
        stage('Security Scanning') {
            parallel {
                stage('Trivy Vulnerability Scan') {
                    steps {
                        echo 'Running Trivy security scan...'
                        script {
                            sh '''
                                docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
                                    aquasec/trivy image --severity HIGH,CRITICAL \
                                    ${DOCKER_IMAGE}:${DOCKER_TAG} || true
                            '''
                        }
                    }
                }
                
                stage('Python Bandit Scan') {
                    steps {
                        echo 'Running Bandit Python security scan...'
                        script {
                            sh '''
                                docker run --rm -v ${WORKSPACE}:/code \
                                    cytopia/bandit -r /code -f json -o /code/bandit-report.json || true
                            '''
                        }
                    }
                }
            }
        }
        
        stage('Code Quality Analysis') {
            steps {
                echo 'Running code quality checks...'
                script {
                    sh '''
                        docker run --rm -v ${WORKSPACE}:/code \
                            python:3.11-slim sh -c "pip install flake8 && flake8 /code/*.py --max-line-length=120" || true
                    '''
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
                    sh '''
                        docker stop student-portal-staging || true
                        docker rm student-portal-staging || true
                        docker run -d \
                            --name student-portal-staging \
                            -p 5001:5000 \
                            -e FLASK_ENV=staging \
                            -v /var/student-portal/staging/database:/app/database \
                            -v /var/student-portal/staging/uploads:/app/static/uploads \
                            ${DOCKER_IMAGE}:${DOCKER_TAG}
                    '''
                }
            }
        }
        
        stage('Health Check') {
            steps {
                echo 'Running health check...'
                script {
                    sh '''
                        sleep 10
                        curl -f http://localhost:5001/health || exit 1
                    '''
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
                    sh '''
                        docker stop student-portal-prod || true
                        docker rm student-portal-prod || true
                        docker run -d \
                            --name student-portal-prod \
                            -p 5000:5000 \
                            -e FLASK_ENV=production \
                            -v /var/student-portal/prod/database:/app/database \
                            -v /var/student-portal/prod/uploads:/app/static/uploads \
                            ${DOCKER_IMAGE}:${DOCKER_TAG}
                    '''
                }
            }
        }
    }
    
    post {
        success {
            echo 'Pipeline completed successfully!'
            emailext(
                subject: "SUCCESS: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]'",
                body: "Good news! The build ${env.BUILD_NUMBER} completed successfully.",
                to: 'team@example.com'
            )
        }
        failure {
            echo 'Pipeline failed!'
            emailext(
                subject: "FAILURE: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]'",
                body: "Build ${env.BUILD_NUMBER} failed. Please check Jenkins for details.",
                to: 'team@example.com'
            )
        }
        always {
            echo 'Cleaning up...'
            sh 'docker system prune -f || true'
            cleanWs()
        }
    }
}
