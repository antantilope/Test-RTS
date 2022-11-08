
import { Injectable } from '@angular/core'
import { HttpClient } from '@angular/common/http';
import { io, Socket } from 'socket.io-client'
import { Subject } from 'rxjs'

import { StartCountdownPayload } from './models/startcountdown-payload.model'
import { AllChatMessage } from './models/allchat-message.model';
import { FrameData, LiveGameDetails } from './models/apidata.model';


@Injectable({
  providedIn: 'root'
})
export class ApiService {

  private socket: Socket

  private EVENT_FRAMEDATA: string = "framedata"
  public frameDataEvent: Subject<void> = new Subject()
  public frameData: FrameData | null = null
  public liveGameDetails: LiveGameDetails | null = null

  public lastShockwaveFrame : number | null = null

  private EVENT_STARTCOUNTDOWN: string = "startcountdown"
  public startCountdownEvent: Subject<StartCountdownPayload> = new Subject()

  private EVENT_SIGKILL: string = "sigkill"
  public sigkillEvent: Subject<void> = new Subject()

  private EVENT_PUBMSG = "pubmsg"
  public pubmsgEvent: Subject<AllChatMessage> = new Subject()

  private EVENT_GAME_COMMAND = "gc"
  private allowedDeadCommands = ["leave_game"]

  constructor(
    private _http: HttpClient,
  ) {

    console.log("ApiService::constructor")

    this.fetchLiveDetails()

    const url: string = document.location.origin.replace(/^https?/, 'ws') // TODO: remove "s" from regex?
    console.log("ApiService::constructor connecting to socket server on " + url)
    this.socket = io(url)

    this.socket.on("connect", () => {
      console.log("Socket Connected!")
    })

    this.socket.on(this.EVENT_FRAMEDATA, (data: FrameData) => {
      this.frameData = data
      this.frameDataEvent.next()
      if(data.game_frame % 400 === 0) {
        console.log({framedata: data})
      }
    })

    this.socket.on(this.EVENT_STARTCOUNTDOWN, (data: StartCountdownPayload) => {
      this.startCountdownEvent.next(data)
    })

    this.socket.on(this.EVENT_SIGKILL, ()=>{
      this.sigkillEvent.next()
      setTimeout(() => {
        location.reload()
      }, 750);
    })

    this.socket.on(this.EVENT_PUBMSG, (message: AllChatMessage)=>{
      this.pubmsgEvent.next(message);
    })
  }

  public async sendPublicMessage(msg: string) {
    this.socket.emit(this.EVENT_PUBMSG, msg)
  }

  public async get(url:string) {
    return this._http.get(url).toPromise();
  }

  public async post(url:string, data: any){
    return this._http.post(url, data).toPromise();
  }

  async emitGameCommand(command: string, data: any) {
    if(
      (this.frameData && this.frameData.ship.alive)
      || this.allowedDeadCommands.indexOf(command) != -1
    ) {
      this.socket.emit(this.EVENT_GAME_COMMAND, command, data)
    } else {
      console.warn("not emitting game command, no frame data or ship is dead.")
    }
  }

  private async fetchLiveDetails() {
    console.log("fetchLiveDetails()")
    // @ts-ignore
    const resp: LiveGameDetails = await this.get("/api/game/live-details")
    console.log({resp})
    this.liveGameDetails = resp;
    console.log("fetchLiveDetails() DONE")
  }

}
