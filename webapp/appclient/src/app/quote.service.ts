import { Injectable } from '@angular/core';



export class QuoteDetails {
  lines: string[]
  author?: string
  use?: boolean
}


@Injectable({
  providedIn: 'root'
})
export class QuoteService {

  private quotes: QuoteDetails[] = [
    {
      lines:[
        "Live by the death ray,",
        "die by the death ray."
      ],
    },
    {
      lines: [
        "Only the dead have seen",
        "the end of the space war.",
      ],
      author: "Space Lt. General PattonBot",
    },
    {
      lines: [
        "I have never advocated space war",
        "except as a means to mine space ore.",
      ],
      author: "President GrayBot DrillBit v4.61.2",
    },
    {
      lines: [
        "To secure space ore",
        "is to prepare for space war.",
      ],
      author: "President GrayBot DrillBit v4.61.2",
    },
    {
      lines: [
        "It is an unfortunate fact that we",
        "can only secure space ore by",
        "preparing for space war.",
      ],
      author: "President GrayBot DrillBit v4.61.2",
    },
    {
      lines: [
        "I hope I never have to fight in space war.",
      ],
      author: "President GrayBot DrillBit v4.61.2",
    },
    {
      lines: [
        "All space warfare is based",
        "on space deception.",
      ],
      author:"Sir Space Bot The V3.773.22",
    },
    {
      lines: [
        "Space war is hell.",
      ],
    },
    {
      lines: [
        "Space war is god's way of",
        "teaching humans astonomy.",
      ],
    },
    {
      lines: [
        "Carbon life is an infection.",
      ],
      author:"Auto Hunter Bot V1.11.34",
    },
    {
      lines: [
        "There is no murder is space.",
      ],
      author:"TrialBot V12.0.6 Esq.",
    },
    {
      lines: [
        "War settles nothing.",
        "Space war settles space ore disputes.",
      ],
      author:"TrialBot V12.0.6 Esq.",
    },
    {
      lines: [
        "Space war is the unfolding of calculations."
      ],
      author: "Lt. Colonel LogisticsBot S/N 635112",
    },
    {
      lines: [
        "No space war is over",
        "until the enemy is melted.",
      ],
      author: "Captin Oxhator ControlBot V1.04.1",
    },
    {
      lines: [
        "Ore coin is worth dieing over.",
      ],
      author:"Channel 9 Fiancial News AnchorBot",
    },
    {
      lines: [
        "Shoot first and don't miss.",
      ],
      author: "Type 27 Ship Instruction Manual",
    },
    {
      lines: [
        "Space fuel is terribly flammible."
      ],
      author: "Type 27 Ship Instruction Manual",
    },
    {
      lines: [
        "If the ship is aflame then abandon ship.",
      ],
      author: "Type 27 Ship Instruction Manual",
      use: true
    },
    {
      lines: [
        "The energy beam is not a toy.",
      ],
      author: "Type 27 Ship Instruction Manual",
    },
  ]

  constructor() { }

  public getQuote(): QuoteDetails {
    const toUse = this.quotes.find(q => q.use)
    if(toUse) {
      return toUse
    }
    return this.quotes[Math.floor(Math.random()* this.quotes.length)]
  }
}
