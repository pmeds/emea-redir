pipeline {
  agent any
  stages {
    stage('get excel and python script') {
      steps {
        echo 'Getting the excel and python files'
        sh '''ls -la
chmod 754 create_json_buckets.py
chmod 754 staging_upload_json_buckets.py
chmod 754 staging_url_validation.py
mkdir json_buckets_with_jenkins
wget https://emea-redirects.us-southeast-1.linodeobjects.com/sample_modified_clean_csv_file.tgz'''
      }
    }


    stage('Creating json buckets') {
      steps {
        echo 'Generating all buckets'
        script {
          if (fileExists('json_buckets_with_jenkins')) {
            sh 'tar -xzfv sample_modified_clean_csv_file.tgz'
            sh 'python3 create_json_buckets.py'
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
          if (fileExists('json_buckets_with_jenkins')) {
            sh 'echo "testing uploaded rules"'
            sh 'python3 staging_url_validation.py'
          }
        }

      }
    }

    stage('Delete environment') {
      steps {
        cleanWs(cleanWhenAborted: true, cleanWhenFailure: true, cleanWhenNotBuilt: true, cleanWhenSuccess: true)
      }
    }

  }
}
