## About

Code and implementation of an agent/model harness api.

Runs regular chatting with models, but the main point is testing models with requests using different prompt techniques.

### Usage

Make a conda environment, use the environment.yml to get the modules.

Run the main.py file. The loop should be implemented:

  1. Choose your mode (Chatting or Testing)
     
     1.1 If chatting, the chat will not be saved, evaluated or loaded. It just serves as a way to communicate with the model, check API status and OpenRouter's availability

  2. Select the model you want to use (if OpenRouter removed it from the free model selection, there's nothing I can do except change the model list or add the option to input a valid model id)
  3. Select a test (the test title is a description)
  4. Select a technique to use (the techniques are set for each test, all tests should have them)
  5. Select how many rounds you want to run (repetitions), which I thought would add variability but it does not really change the answers the model returns
  6. Choose if you want to save the results, which will be saved into data/results/test_id/technique_id/model_id/

Errors should be catched, some stop the compilation others just run in a loop for reinput.

By default the answers in testing are not printed, only metrics + scores and such are shown to bloat the output the least.
The resulting file is a json that contains almost all the information produced during the test:

  - Test
  - Technique
  - Initial prompts + expected answers
  - Score criterions
  - Evaluators
  - Scores
  - Metrics
  - Summary of the result

These results will be used to compare the model performances and technique variability.

That's about it. Any debug prints and comments should be removed by the end of the project, and the code cleaned (maybe?).
