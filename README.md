# EmptorAssignment

Install serverless: https://www.serverless.com/

Deploy with `$ sls deploy`

Invoke functions available:

`input_title`
`title_commit`
`get_title`

Example:

`serverless invoke -f input_title  -d '{"url": "https://github.com"}' -l`