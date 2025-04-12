# Changelog

## [1.1.0](https://github.com/johnjaredprater/gym_track_core/compare/v1.0.1...v1.1.0) (2025-04-12)


### Features

* allow an admint to add or delete an exercise ([f8dc3de](https://github.com/johnjaredprater/gym_track_core/commit/f8dc3deee5be0a9dfe2f8a30b37dd12f249508a3))

## [1.0.1](https://github.com/johnjaredprater/gym_track_core/compare/v1.0.0...v1.0.1) (2024-12-14)


### Bug Fixes

* use the Digital Ocean DB host & port ([0d21b64](https://github.com/johnjaredprater/gym_track_core/commit/0d21b649b1eb9a4fb57f91ba0cede32b410971eb))

## [1.0.0](https://github.com/johnjaredprater/gym_track_core/compare/v0.10.0...v1.0.0) (2024-12-12)


### ⚠ BREAKING CHANGES

* create DB & tables on start-up

### Features

* create DB & tables on start-up ([846ffa2](https://github.com/johnjaredprater/gym_track_core/commit/846ffa237b531636678d9a571c37d82ff0695785))

## [0.10.0](https://github.com/johnjaredprater/gym_track_core/compare/v0.9.0...v0.10.0) (2024-11-04)


### Features

* Support date column in the API ([4542302](https://github.com/johnjaredprater/gym_track_core/commit/454230237a19e13bf0038d2103c478ccfab89857))

## [0.9.0](https://github.com/johnjaredprater/gym_track_core/compare/v0.8.1...v0.9.0) (2024-11-04)


### Features

* add alembic to manage migrations and add a date column to workouts ([bb8aa1a](https://github.com/johnjaredprater/gym_track_core/commit/bb8aa1a4677f66e835291a8f0a31899d66dc075f))

## [0.8.1](https://github.com/johnjaredprater/gym_track_core/compare/v0.8.0...v0.8.1) (2024-10-13)


### Bug Fixes

* post RPE correctly ([b146342](https://github.com/johnjaredprater/gym_track_core/commit/b14634267b822a4e494ac4f770e0982f67e7ff87))

## [0.8.0](https://github.com/johnjaredprater/gym_track_core/compare/v0.7.1...v0.8.0) (2024-10-07)


### Features

* Allow updating a workout ([965f5a3](https://github.com/johnjaredprater/gym_track_core/commit/965f5a3c7c5e946fb8203f7814a51c68da36f964))

## [0.7.1](https://github.com/johnjaredprater/gym_track_core/compare/v0.7.0...v0.7.1) (2024-10-01)


### Bug Fixes

* Restore missing imports ([7c60dc8](https://github.com/johnjaredprater/gym_track_core/commit/7c60dc83cad03f7a2bcbfcdb3c7a40081110a9da))

## [0.7.0](https://github.com/johnjaredprater/gym_track_core/compare/v0.6.3...v0.7.0) (2024-10-01)


### Features

* add workout dom and endpoints to get, create & delete ([128e4e0](https://github.com/johnjaredprater/gym_track_core/commit/128e4e05495d765ef23cd7f6c3ab3f282e26527c))

## [0.6.3](https://github.com/johnjaredprater/gym_track_core/compare/v0.6.2...v0.6.3) (2024-09-25)


### Bug Fixes

* decode kubernetes secret in a rather hacky way ([e9cf297](https://github.com/johnjaredprater/gym_track_core/commit/e9cf2970c64edbc4d191b8afe692fbe6139e2612))

## [0.6.2](https://github.com/johnjaredprater/gym_track_core/compare/v0.6.1...v0.6.2) (2024-09-25)


### Bug Fixes

* Point towards the right DB and update the secret names ([103b978](https://github.com/johnjaredprater/gym_track_core/commit/103b978acdcc65d30576c58077d7a07d774ab3e7))

## [0.6.1](https://github.com/johnjaredprater/gym_track_core/compare/v0.6.0...v0.6.1) (2024-09-22)


### Bug Fixes

* Don't create a DB by default for now ([144d215](https://github.com/johnjaredprater/gym_track_core/commit/144d215c232eb96f7468879847764abf3ce96c22))

## [0.6.0](https://github.com/johnjaredprater/gym_track_core/compare/v0.5.3...v0.6.0) (2024-09-22)


### Features

* Require & verify auth for endpoints by default with some explicit exceptions ([b8ee8f1](https://github.com/johnjaredprater/gym_track_core/commit/b8ee8f12438274aa197b00182eb2a86628ad7876))

## [0.5.3](https://github.com/johnjaredprater/gym_track_core/compare/v0.5.2...v0.5.3) (2024-09-17)


### Bug Fixes

* allow local fallback ([e4bfdd9](https://github.com/johnjaredprater/gym_track_core/commit/e4bfdd9fb78e0c53e8523febf8d3e577c5cd7a43))
* create the DB ([757a1c1](https://github.com/johnjaredprater/gym_track_core/commit/757a1c1d1fbb85a09d54d9a939514f2c985908e8))

## [0.5.2](https://github.com/johnjaredprater/gym_track_core/compare/v0.5.1...v0.5.2) (2024-09-17)


### Bug Fixes

* keep the base url as a health check ([ed9930c](https://github.com/johnjaredprater/gym_track_core/commit/ed9930c6adde04c875bb09bba27b4dc7191f3911))

## [0.5.1](https://github.com/johnjaredprater/gym_track_core/compare/v0.5.0...v0.5.1) (2024-09-17)


### Bug Fixes

* add debug ([4747d13](https://github.com/johnjaredprater/gym_track_core/commit/4747d13306f406d16fccb7a6060acbddcc01c056))

## [0.5.0](https://github.com/johnjaredprater/gym_track_core/compare/v0.4.1...v0.5.0) (2024-09-16)


### Features

* connect to the RDS DB ([eb798c8](https://github.com/johnjaredprater/gym_track_core/commit/eb798c89ac5bfd456d8dcd2429dde82aa9839ffe))

## [0.4.1](https://github.com/johnjaredprater/gym_track_core/compare/v0.4.0...v0.4.1) (2024-09-16)


### Bug Fixes

* structure yaml properly ([870a05a](https://github.com/johnjaredprater/gym_track_core/commit/870a05aa3f93a6bd4d0f5e0697b2bd07f36235f7))

## [0.4.0](https://github.com/johnjaredprater/gym_track_core/compare/v0.3.0...v0.4.0) (2024-09-16)


### Features

* add DB credentials ([d53ad64](https://github.com/johnjaredprater/gym_track_core/commit/d53ad64a8e9e221fe3b5cd538063086471f0119f))

## [0.3.0](https://github.com/johnjaredprater/gym_track_core/compare/v0.2.0...v0.3.0) (2024-09-14)


### Features

* add generated OpenAPI schema and version endpoint ([86343b2](https://github.com/johnjaredprater/gym_track_core/commit/86343b25b844f3d74d7e643cb6aab049e1ffc91b))

## [0.2.0](https://github.com/johnjaredprater/gym_track_core/compare/v0.1.0...v0.2.0) (2024-09-14)


### Features

* expose internally via a service ([3d1593a](https://github.com/johnjaredprater/gym_track_core/commit/3d1593a2530f23ee706efc686714c62c9eb1da46))


### Bug Fixes

* add api endpoint ([e931c90](https://github.com/johnjaredprater/gym_track_core/commit/e931c90e43e169b127f7dfe3584d6c10c86209ab))

## [0.1.0](https://github.com/johnjaredprater/gym_track_core/compare/v0.0.0...v0.1.0) (2024-09-11)


### Features

* deploy 1 replica ([367a7a0](https://github.com/johnjaredprater/gym_track_core/commit/367a7a0f1432dedb2440d7eb3c5c220136c38f33))

## 0.0.0 (2024-09-09)


### Miscellaneous Chores

* initial commit ([1bab8e6](https://github.com/johnjaredprater/gym_track_core/commit/1bab8e622376a51011221766f58e63ae15dc3919))
