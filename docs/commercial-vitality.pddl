; 전력 사용량으로 상권 활력을 읽는 도메인.
; 설명 문서는 docs/PDDL.md. 이 파일이 플래너 입력이다.
; 가스·공실은 이번 수급에서 빠진다. 업종 전력은 매출로 추론하고 inferred 로 표시한다.

(define (domain commercial-vitality)
  (:requirements :typing :fluents :negative-preconditions :action-costs)

  (:types
    actor region trade-area industry dataset layer product
  )

  (:predicates
    (needs-intel ?a - actor)
    (hard-to-survey ?r - region)
    (ingested ?d - dataset)
    (omitted ?d - dataset)
    (has-energy ?r - region)
    (has-commerce ?r - region)
    (mapped ?r - region)
    (indexed ?r - region)
    (searchable ?r - region)
    (cataloged ?d - dataset)
    (sim-ready ?i - industry)
    (inferred ?i - industry)
    (subscribed ?a - actor)
    (offered ?p - product)
    (covers ?l - layer ?r - region)
  )

  (:functions
    (vitality ?r - region)
    (vacancy-risk ?r - region)
    (energy-kwh ?i - industry)
    (energy-cost ?i - industry)
    (total-cost)
  )

  (:action ingest-public-data
    :parameters (?d - dataset ?r - region)
    :precondition (and
      (not (ingested ?d))
      (not (omitted ?d))
      (hard-to-survey ?r))
    :effect (and
      (ingested ?d)
      (has-energy ?r)
      (has-commerce ?r)
      (increase (total-cost) 1))
  )

  (:action fuse-district-index
    :parameters (?r - region ?power ?sales ?flow ?weather - dataset)
    :precondition (and
      (ingested ?power)
      (ingested ?sales)
      (ingested ?flow)
      (ingested ?weather)
      (has-energy ?r)
      (has-commerce ?r)
      (not (indexed ?r)))
    :effect (and
      (indexed ?r)
      (increase (vitality ?r) 1)
      (increase (total-cost) 1))
  )

  (:action paint-heatmap
    :parameters (?r - region ?l - layer)
    :precondition (and (indexed ?r) (not (mapped ?r)))
    :effect (and
      (mapped ?r)
      (searchable ?r)
      (covers ?l ?r)
      (increase (total-cost) 1))
  )

  (:action expose-catalog
    :parameters (?d - dataset)
    :precondition (and (ingested ?d) (not (cataloged ?d)))
    :effect (and
      (cataloged ?d)
      (increase (total-cost) 1))
  )

  (:action simulate-startup
    :parameters (?i - industry ?r - region ?sales - dataset)
    :precondition (and
      (indexed ?r)
      (ingested ?sales)
      (not (sim-ready ?i)))
    :effect (and
      (sim-ready ?i)
      (inferred ?i)
      (increase (energy-kwh ?i) 1)
      (increase (energy-cost ?i) 1)
      (increase (total-cost) 1))
  )

  (:action package-revenue
    :parameters (?p - product ?a - actor)
    :precondition (and
      (needs-intel ?a)
      (not (offered ?p)))
    :effect (and
      (offered ?p)
      (subscribed ?a)
      (increase (total-cost) 1))
  )
)
