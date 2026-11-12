; MVP problem for the 25 Seoul districts, July 2025 through June 2026.
; 서울 25개 구 MVP. 창은 2025-07 ~ 2026-06.
; 골목 점은 자치구 점수와 같다. 가스·공실·건축물대장·전국 상가는 omitted.

(define (problem vitality-mvp)
  (:domain commercial-vitality)

  (:objects
    local-gov owner realtor - actor
    seoul - region
    alley downtown suburb - trade-area
    cafe korean chicken pub cvs beauty academy retail gym pharmacy - industry
    kepco-contract seoul-store seoul-sales seoul-flpop weather tariff geo - dataset
    gas vacancy building-ledger national-stores - dataset
    heatmap - layer
    short-pack monthly banner - product
  )

  (:init
    (needs-intel local-gov)
    (needs-intel owner)
    (needs-intel realtor)
    (hard-to-survey seoul)

    (omitted gas)
    (omitted vacancy)
    (omitted building-ledger)
    (omitted national-stores)

    (= (vitality seoul) 0)
    (= (vacancy-risk seoul) 0)
    (= (energy-kwh cafe) 0)
    (= (energy-kwh korean) 0)
    (= (energy-kwh chicken) 0)
    (= (energy-kwh pub) 0)
    (= (energy-kwh cvs) 0)
    (= (energy-kwh beauty) 0)
    (= (energy-kwh academy) 0)
    (= (energy-kwh retail) 0)
    (= (energy-kwh gym) 0)
    (= (energy-kwh pharmacy) 0)
    (= (energy-cost cafe) 0)
    (= (energy-cost korean) 0)
    (= (energy-cost chicken) 0)
    (= (energy-cost pub) 0)
    (= (energy-cost cvs) 0)
    (= (energy-cost beauty) 0)
    (= (energy-cost academy) 0)
    (= (energy-cost retail) 0)
    (= (energy-cost gym) 0)
    (= (energy-cost pharmacy) 0)
    (= (total-cost) 0)
  )

  (:goal (and
    (cataloged kepco-contract)
    (cataloged seoul-store)
    (cataloged seoul-sales)
    (mapped seoul)
    (indexed seoul)
    (searchable seoul)
    (sim-ready cafe)
    (inferred cafe)
    (offered short-pack)
    (offered monthly)
  ))

  (:metric minimize (total-cost))
)
