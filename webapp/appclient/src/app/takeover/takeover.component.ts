import { Component, OnInit } from '@angular/core';
import { AssetService } from '../asset.service';
import { SoundService } from '../sound.service';
import { TakeoverService } from '../takeover.service';


@Component({
  selector: 'app-takeover',
  templateUrl: './takeover.component.html',
  styleUrls: ['./takeover.component.css']
})
export class TakeoverComponent implements OnInit {

  constructor(
    public takeover: TakeoverService,
    private _sound: SoundService, // We want sounds to download immediatly
    private _asset: AssetService, // We want images to download immediatly
  ) {
    console.log("TakeoverComponent::constructor");
  }

  ngOnInit(): void {
  }

}
