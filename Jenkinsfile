pipeline {
    agent none
    environment {
    WORKSPACE_DIR = "/home/jenkins/workspace/Taxonomy_NEW"
    MASTER_WORKSPACE_DIR = "/var/lib/jenkins/workspace/Taxonomy_NEW"
    DB_PATH       = "/home/jenkins/workspace/Taxonomy_NEW/output/metadata.db"
    GRAFANA_FORENSIC_DIR = "/var/lib/grafana/forensic"
    FORENSIC_AGENT = "/home/jenkins/forensic/collect_agent.py"
    LOKI_URL = "http://172.16.0.4:3100/loki/api/v1/push"
    MONGO_URI = credentials('mongo-atlas-secret') // Jenkins credential ID
    }
  stages {
    stage('Deploy Agent Script & Collect Logs') {
      agent { label 'agent' }
      steps {
      sh '''
        chmod -R 700 /home/jenkins/workspace/ || true
        echo "Copying agent to target..."
        scripts/collect_agent.py
      '''
    }
  }
    stage('Prioritize Artifacts') {
      agent { label 'agent' }
      steps {
        sh 'python3 scripts/prioritize.py --in ${WORKSPACE_DIR}/output/artifacts.json --out ${WORKSPACE_DIR}/output/priority_list.json'
      }
    }
    stage('Format and Split Logs') {
        agent { label 'agent' }
        steps {
        sh 'python3 scripts/format_json.py --in ${WORKSPACE_DIR}/output/artifacts.json --out ${WORKSPACE_DIR}/output/formatted_logs.json'
        sh 'python3 scripts/split_formatted_logs.py'
        stash name: 'artifacts', includes: 'output/**'    
      }
    }   


        stage('Format Logs') {
            agent { label 'master' } 
            steps {
                sh """
                mkdir -p output/loki_logs output/mongo_logs
                for file in split_logs/*.json; do
                    echo "[+] Processing $file"
                    python3 scripts/format_for_loki.py --in $file --out-dir output/loki_logs
                    python3 scripts/format_for_mongo.py --in $file --out-dir output/mongo_logs
                done
                """
            }
        }

        stage('Push to Loki') {
            agent { label 'master' }             
            steps {
                sh """
                for file in output/loki_logs/*.json; do
                    echo "[+] Pushing $file to Loki..."
                    curl -s -X POST -H "Content-Type: application/json" \
                        --data-binary @$file \
                        http://172.16.0.4:3100/loki/api/v1/push || true
                done
                """
            }
        }
        stage('Push to MongoDB') {
            agent { label 'master' }             
            steps {
                withCredentials([string(credentialsId: 'mongo-uri', variable: 'MONGO_URI')]) {
                    sh """
                    python3 scripts/push_to_mongo.py \
                        --mongo-uri "$MONGO_URI" \
                        --db TaxonomyDB \
                        --collection Artifacts \
                        --in-dir output/mongo_logs
                    """
                }
            }
        }
#################################################################
        // stage('Format Logs for Loki and MongoDB') {
        //     agent { label 'master' }  
        //     steps {
        //         unstash 'artifacts'
        //         archiveArtifacts artifacts: 'output/**', fingerprint: true                
        //         sh '''
        //             mkdir -p ${MASTER_WORKSPACE_DIR}/output/loki_logs
        //             echo "[+] Formatting logs for Loki"
        //             for f in ${MASTER_WORKSPACE_DIR}/output/split_logs/*.json; do
        //                  base=$(basename "$f" .json)
        //                  out="${MASTER_WORKSPACE_DIR}/output/loki_logs/${base}_loki.json"
        //                  echo "[+] Formatting $f -> $out"
        //                  python3 scripts/format_for_loki.py --in "$f" --out "$out"
        //             done 
        //         '''
        //         archiveArtifacts artifacts: 'output/**', fingerprint: true                
        //     }
        // }
        // stage('Push Logs to Loki') {
        //     agent { label 'master' }              
        //     steps {
        //          sh '''
        //               for f in ${WORKSPACE}/output/loki_logs/*_loki.json; do
        //                    echo "[+] Pushing $f to Loki..."
        //                    python3 scripts/push_to_loki.py --in "$f" --loki-url ${LOKI_URL}
        //               done
        //          '''
        //     }
        // }
        // stage('Push to MongoDB') {
        //     agent { label 'master' }              
        //     steps {
        //           withCredentials([string(credentialsId: 'mongo-atlas-secret', variable: 'MONGO_URI')]) {
        //           // sh 'python3 scripts/push_to_mongo.py --mongo-uri "$MONGO_URI" --db "TaxonomyDB" --collection "Artifacts" --in-dir "${WORKSPACE}/output/loki_logs"'
        //           sh 'python3 scripts/push_to_mongo.py --mongo-uri "$MONGO_URI" --db TaxonomyDB --collection Artifacts --in-dir output/mongo_logs'    
        //           }
        //     }
        // }
        stage('Visualization') {
            agent { label 'master' }  
            steps {
                sh """
                    echo "[+] Visualization available in Grafana + Loki dashboards"
                    echo "[+] MongoDB Atlas can be queried for metadata insights"
                """
            }
        }
    // stage('Upload Reports to Azure Storage') {
    //   agent { label 'master' }    
    //   steps {
    //         script {
    //         withCredentials([
    //             string(credentialsId: 'TAXONOMY_STORAGE_ACCOUNT_KEY', variable: 'TAXONOMY_STORAGE_ACCOUNT_KEY')
    //                 ]) {
    //             sh '''
    //             # Set variables - REPLACE WITH YOUR ACTUAL STORAGE KEY
    //             STORAGE_ACCOUNT="taxonomystorage123"
    //             CONTAINER="reports"
    //             az storage blob upload-batch --account-name $STORAGE_ACCOUNT --account-key "$TAXONOMY_STORAGE_ACCOUNT_KEY" --destination "reports/builds/$BUILD_NUMBER" --source output --overwrite
    //             az storage blob upload-batch --account-name $STORAGE_ACCOUNT --account-key "$TAXONOMY_STORAGE_ACCOUNT_KEY" --destination "reports/latest" --source output --overwrite
    //             '''
    //         }  
    //   }
    // }        
    // }
  }
}
