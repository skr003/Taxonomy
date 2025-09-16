
pipeline {
  agent any
  environment {
    WORKSPACE_DIR = "${env.WORKSPACE}/output"
    DB_PATH       = "${env.WORKSPACE}/output/metadata.db"
    GRAFANA_FORENSIC_DIR = "/var/lib/grafana/forensic"
  }

  stages {
    stage('Initialize') {
      steps {
        echo 'Preparing workspace...'
        sh 'mkdir -p ${WORKSPACE_DIR}'
        sh 'python3 scripts/initialize.py --workspace ${WORKSPACE_DIR}'
      }
    }

    stage('Deploy Agent Script & Ensure Target Dir') {
      steps {
        withCredentials([
          string(credentialsId: 'TARGET_IP', variable: 'TARGET_IP'),
          string(credentialsId: 'SSH_CRED_ID', variable: 'SSH_CRED_ID')
        ]) {
          withCredentials([sshUserPrivateKey(credentialsId: "${SSH_CRED_ID}", keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER')]) {
            sh '''
              echo "Creating target forensic dir..."
              ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SSH_USER@$TARGET_IP "mkdir -p /home/$SSH_USER/forensic/output && chmod -R 700 /home/$SSH_USER/forensic || true"
              echo "Copying agent to target..."
              scp -i $SSH_KEY -o StrictHostKeyChecking=no scripts/collect_agent.py $SSH_USER@$TARGET_IP:/home/$SSH_USER/forensic/collect_agent.py
              ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SSH_USER@$TARGET_IP "chmod +x /home/$SSH_USER/forensic/collect_agent.py"
            '''
          }
        }
      }
    }

    stage('Run Agent on Target (collect live data)') {
      steps {
        withCredentials([
          string(credentialsId: 'TARGET_IP', variable: 'TARGET_IP'),
          string(credentialsId: 'SSH_CRED_ID', variable: 'SSH_CRED_ID')
        ]) {
          withCredentials([sshUserPrivateKey(credentialsId: "${SSH_CRED_ID}", keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER')]) {
            sh '''
              echo "Running agent remotely..."
              ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SSH_USER@$TARGET_IP "python3 /home/$SSH_USER/forensic/collect_agent.py"
              echo "Copying artifacts back to controller workspace..."
              scp -i $SSH_KEY -o StrictHostKeyChecking=no $SSH_USER@$TARGET_IP:/home/jenkins/output/artifacts.json ${WORKSPACE_DIR}/artifacts.json
            '''
          }
        }
      }
    }

    stage('Prioritize Artifacts') {
      steps {
        sh 'python3 scripts/prioritize.py --in ${WORKSPACE_DIR}/artifacts.json --out ${WORKSPACE_DIR}/priority_list.json'
      }
    }

    stage('Format Logs') {
      steps {
        sh 'python3 scripts/format_json.py --in ${WORKSPACE_DIR}/artifacts.json --out ${WORKSPACE_DIR}/formatted_logs.json'
        sh 'python3 scripts/split_formatted_logs.py'
      }
    }  

    stage('Store Metadata') {
      steps {
        sh 'python3 scripts/store_metadata.py --db ${DB_PATH} --meta ${WORKSPACE_DIR}/priority_list.json'
        archiveArtifacts artifacts: 'output/**', fingerprint: true

      }
    }

    stage('Upload Reports to Azure Storage') {
      steps {
            script {
            withCredentials([
                string(credentialsId: 'TAXONOMY_STORAGE_ACCOUNT_KEY', variable: 'TAXONOMY_STORAGE_ACCOUNT_KEY')
                    ]) {
                sh '''
                # Set variables - REPLACE WITH YOUR ACTUAL STORAGE KEY
                STORAGE_ACCOUNT="taxonomystorage123"
                CONTAINER="reports"

                az storage blob upload-batch --account-name $STORAGE_ACCOUNT --account-key "$TAXONOMY_STORAGE_ACCOUNT_KEY" --destination "reports/builds/$BUILD_NUMBER" --source forensic_workspace
                az storage blob upload-batch --account-name $STORAGE_ACCOUNT --account-key "$TAXONOMY_STORAGE_ACCOUNT_KEY" --destination "reports/latest" --source forensic_workspace


                #for f in forensic_workspace/*.json; do
                #    az storage blob upload --account-name $STORAGE_ACCOUNT --container-name $CONTAINER --file "$f" --name "builds/$BUILD_NUMBER/$fname" --account-key "$TAXONOMY_STORAGE_ACCOUNT_KEY" --overwrite
                #    az storage blob upload --account-name $STORAGE_ACCOUNT --container-name $CONTAINER --file "$f" --name "latest/$fname" --account-key "$TAXONOMY_STORAGE_ACCOUNT_KEY" --overwrite                    
                #done
          
                # Upload to build-specific path
                #az storage blob upload --container-name $CONTAINER --name "builds/$BUILD_NUMBER/$fname" --file "$f"--account-name $STORAGE_ACCOUNT --account-key "$TAXONOMY_STORAGE_ACCOUNT_KEY" --overwrite
                #az storage blob upload --container-name $CONTAINER --name "builds/$BUILD_NUMBER/formatted_logs.json" --file forensic_workspace/formatted_logs.json --account-name $STORAGE_ACCOUNT --account-key "$TAXONOMY_STORAGE_ACCOUNT_KEY" --overwrite

                # Upload to 'latest' path
                #az storage blob upload --container-name $CONTAINER --name "latest/$fname" --file "$f" --account-name $STORAGE_ACCOUNT --account-key "$TAXONOMY_STORAGE_ACCOUNT_KEY" --overwrite
                #az storage blob upload --container-name $CONTAINER --name "latest/formatted_logs.json" --file forensic_workspace/formatted_logs.json --account-name $STORAGE_ACCOUNT --account-key "$TAXONOMY_STORAGE_ACCOUNT_KEY" --overwrite
                '''
            }  
      }
    }        
    }
    
    stage('Export Mindmap') {
      steps {
        sh 'python3 scripts/mindmap_export.py --in ${WORKSPACE_DIR}/formatted_logs.json --out ${WORKSPACE_DIR}/mindmap.json'
      }
    }
  }
}
