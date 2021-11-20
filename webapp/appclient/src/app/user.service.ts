import { Injectable } from '@angular/core';
import { ApiService } from './api.service';




@Injectable({
  providedIn: 'root'
})
export class UserService {

  public handle = ""

  constructor(
    private _api: ApiService,
  ) {
    this.getUsername()
  }

  private async getUsername() {
    let data: any
    try{
      data = await this._api.get("/api/users/details")
    }
    catch (err) {
      console.error(err)
      return
    }
    this.handle = data.handle
  }



}
