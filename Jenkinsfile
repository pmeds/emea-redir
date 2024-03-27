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
                chmod 754 staging_upload_json_buckets.py
                chmod 754 staging_url_validation.py
                mkdir json_buckets_with_jenkins
                mkdir validation_json
                wget https://emea-redirects.us-southeast-1.linodeobjects.com/modified_no_whitespace_clean_csv_file.tgz
                '''
            }
        }

        stage('Creating json buckets') {
            steps {
                echo 'Generating all buckets'
                script {
                    if (fileExists('json_buckets_with_jenkins')) {
                        sh 'tar -xzvf modified_no_whitespace_clean_csv_file.tgz'
                        sh 'python3 create_json_buckets.py'
                        sh 'python3 create_validation_buckets.py'
                    }
                }
            }
        }

        stage('Upload Rule') {
            steps {
                echo 'checking if there is a csv file for games'
                script {
                    if (fileExists('json_buckets_with_jenkins')) {
                        sh 'echo "uploading games rules"'
                        sh 'python3 staging_upload_json_buckets.py'
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
                        sh 'python3 staging_url_validation.py'
                    }
                }
            }
        }
    }

    post {
        always {
            // This will always clean the workspace regardless of the pipeline result
            cleanWs(cleanWhenAborted: true, cleanWhenFailure: true, cleanWhenNotBuilt: true, cleanWhenSuccess: false)
        }
    }
}
