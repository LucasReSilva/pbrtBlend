pipeline {
  agent any
  stages {
    stage('Version check') {
      parallel {
        stage('Version check') {
          steps {
            sh '''/home/lucas/Documentos/TCC/blender-2.79-linux-glibc219-x86_64/blender -v
'''
          }
        }
        stage('') {
          steps {
            sh 'wget https://gist.github.com/LucasReSilva/40dc265ccaaf04dc0cb6e2c81c7dbb0e/raw/8cd87f29a67e496222688eb46281b3ffe5e4c623/PBRTv3_Exemple && pbrt PBRTv3_Exemple'
          }
        }
      }
    }
    stage('Export file') {
      steps {
        sh '''/home/lucas/Documentos/TCC/blender-2.79-linux-glibc219-x86_64/blender -b -f 1
'''
      }
    }
  }
}