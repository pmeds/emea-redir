pipeline {
    agent any

    stages {
        stage('get excel and python script') {
            steps {
                echo 'Getting the excel and python files'
                sh '''
                ls -la
                chmod 754 create_json_buckets.py
                chmod 754 create_validation_buckets.py
                chmod 754 prod_url_validation.py
                mkdir json_buckets_with_jenkins
                mkdir validation_json
                wget https://emea-redirects.us-southeast-1.linodeobjects.com/clean_no_whitespace_updated_urls.tgz
                '''
            }
        }

        stage('Creating json buckets') {
            steps {
                echo 'Generating all buckets'
                script {
                    if (fileExists('json_buckets_with_jenkins')) {
                        sh 'tar -xzvf clean_no_whitespace_updated_urls.tgz'
                        sh 'python3 create_validation_buckets.py'
                    }
                }
            }
        }

        stage('Testing All Redirects') {
            steps {
                echo 'Testing the uploaded rules'
                script {
                    if (fileExists('validation_json')) {
                        sh 'echo "testing uploaded rules"'
                        sh 'python3 prod_url_validation.py'
                    }
                }
            }
        }
    }

    post {
        always {
            // This will always clean the workspace regardless of the pipeline result
            cleanWs(cleanWhenAborted: true, cleanWhenFailure: true, cleanWhenNotBuilt: true, cleanWhenSuccess: true)
        }
    }
}
