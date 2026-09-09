mcweb.native{
  bindingsInit,{
    wmcPlatform:win32,x64
    directShow:enabled
    tvTunerBind:from "sys/tuner/native.dll"
  }
  
  nativeRender(channelID){
    displayBuffer=> allocate:16MB
    frameSync=> 60fps:locked
    return=> bufferHandle
  }
  
  importFromWeb(youtubeURL){
    validateURL=> parsing,auth
    downloadStream=> manifest.m3u8
    transcode=> libavcodec:h264
    insertDB=> wmcdb.sqlite
  }
}

mcweb.webImport{
  handleYoutubeImport(url){
    urlValidator=> checkFormat,parseID
    metaFetch=> yt-dlp:metadata
    qualitySelect=> 480p,720p,1080p
    transcodeJob=> queue:3max
    indexMedia=> wmcdb:add
    return=> importID,progress
  }
  
  streamToWMC(importID){
    getJob=> importQueue[importID]
    bufferStream=> 10MB:chunks
    directShowRender=> tuner:output
    updateProgress=> listener:callback
  }
  
  validateConditions(){
    networkCheck=> ping:youtube.com
    diskSpace=> required:10GB,available
    ffmpegCheck=> version,codecs
    tunerStatus=> connected,ready
    return=> allOK:boolean
  }
}