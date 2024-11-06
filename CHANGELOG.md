# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.1.3] - 2024-11-05

### Changed
- Readme updated

## [0.1.2] - 2024-11-05

### Added
- Context manager support for NeoApiClientSync

### Changed
- Simplified client initialization with environment variables
- Restructured client architecture for better maintainability

### Fixed
- Memory leak in async client shutdown
- Batch processing edge cases
- Connection handling in high-load scenarios

## [0.1.1] - 2024-10-25
### Added
- `check_frequency` parameter to control API request rate
- `NEOAPI_API_KEY` environment variable support
