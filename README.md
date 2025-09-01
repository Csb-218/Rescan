
# Rescan

An AI-powered Applicant Tracking System that analyzes resumes against job descriptions to find the best matches using large language models.


## Features

- PDF extraction and processing for both resumes and job descriptions.
- Advanced document analysis using Ollama LLMs
- Skills matching and scoring
- Education and experience validation
- Improvement suggestions for candidates
- Clean API design with FastAPI
- Containerized deployment with Docker


## Tech Stack

**Server:** FastAPI

**AI/ML** Ollama models(llama3.2) 

**Package manager** uv

**Testing** pytest




## Prerequisites

- Python 3.12+
- Ollama running locally or accessible via network
- Docker (optional, for containerized deployment)
## Run Locally

### Manual Setup
Clone the project

```bash
  git clone https://github.com/Csb-218/Rescan.git
```

Go to the project directory

```bash
  cd rescan
```

```bash
   uv venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

Install dependencies

```bash
  uv sync --locked --no-install-project
```

Start the server

```bash
  fastapi run 
```

### Docker Setup
Build image
```bash
docker build -t rescan .
```

Run the container 

```bash
docker run -p 8000:8000 rescan
```



## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

`OLLAMA_BASE_URL`




## API Endpoints

`/analyze/advanced`
Analyzes a resume against a job description using advanced LLM matching.

Method: `POST`

Parameters:

`jd`: Job description file (PDF)

`resume`: Resume file (PDF)

Returns: JSON with match details, skills comparison, and suggestions
## Usage/Examples

1. Start the application

2. Send a POST request to /analyze/advanced with both resume and job description PDFs.


3. Receive detailed analysis including:
    
    -> Skills matching

    -> Experience validation

    -> Education requirements check

    -> Overall match score
    
    -> Improvement suggestions


## Screenshots

![request](https://res.cloudinary.com/dz3aj0ti8/image/upload/v1756729027/Screenshot_2025-09-01_173722_sts3u1.png)

![response](https://res.cloudinary.com/dz3aj0ti8/image/upload/v1756729027/Screenshot_2025-09-01_173753_ogn5cr.png)
## Running Tests

To run tests, run the following command

```bash
  pytest 
```


## License

[MIT](https://choosealicense.com/licenses/mit/)


## Contributing

Contributions are always welcome!

Please feel free to submit a Pull Request.

