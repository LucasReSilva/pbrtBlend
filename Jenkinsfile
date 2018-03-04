pipeline {
  agent any
  stages {
    stage('Version check') {
      parallel {
        stage('Blender') {
          steps {
            sh '''/home/lucas/Documentos/TCC/blender-2.79-linux-glibc219-x86_64/blender -v
'''
          }
        }
        stage('PBRTv3') {
          steps {
            sh 'wget https://gist.github.com/LucasReSilva/40dc265ccaaf04dc0cb6e2c81c7dbb0e/raw/8cd87f29a67e496222688eb46281b3ffe5e4c623/PBRTv3_Exemple'
            sh 'pbrt PBRTv3_Exemple'
          }
        }
      }
    }
    stage('Export file') {
      steps {
        sh 'wget "https://github.com/LucasReSilva/Cornell-Box/raw/master/Blender%20files/Cycles.blend"'
        sh '/home/lucas/Documentos/TCC/blender-2.79-linux-glibc219-x86_64/blender -b Cycles.blend -f 1 -E CYCLES'
      }
    }
    stage('Render scene') {
      steps {
        sh 'pbrt PBRTv3_Exemple'
      }
    }
    stage('Compare') {
      steps {
        sh 'wget http://www.graphics.cornell.edu/online/box/box.jpg'
        sh ' convert box.jpg -resize 500x500 box_resized.png'
        sh 'composite cornell-box.png box_resized.png -compose difference difference.png'
      }
    }
  }
}