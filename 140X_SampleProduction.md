# 14.0.X sample production

This guide provides a workflow for generating **14.0.X** samples for the **Phase2Spring24** MC campaign in the CMS data production pipeline. The process consists of several key steps.

- **LHE Generation step**: this step involves generating the *Les Houches Event* (LHE) files from pre-compiled **gridpacks** (with MadGraph or another tool), which contain the matrix elements for specific physics processes. Once the LHE files are generated, the subsequent steps are generally independent of the specific physics processes involved. Instead, they are mainly concerned with the campaign-specific configurations and detector simulation settings, which are definited by the particular campaign you're working on (in this case, the Phase2Spring campaign).

    1. Extract the gridpack and run the bash script:
        ```
       tar -xf gridpack.tar.xz
       cd gridpack_directory
       ./runcmsgrid.sh <Number_of_Events> <Random_Seed> <Number_of_Threads>
        ```
    2. Verify that ```cmsgrid_final.lhe``` is created

- **GEN-SIM step**: the *GEN* step runs hadronization and parton showering (e.g, Pythia), so converts partons from the LHE file into realistic hadronic final states, while the *SIM* step uses Geant4 to simulate how particles interact with the CMS detector (so produces hits in the detctor that mimic what would happen in real data). To run this step you need some ```cmsDriver.py``` commands and a ```GenFragment.py```.

    - Go to the [das website](https://cmsweb.cern.ch/das/) and with the query ```dataset=/*/*Phase2Spring24*/*``` find the prep-ID of your dataset  (example: ```TSG-Phase2Spring24DIGIRECOMiniAOD-00122```)
    - Search for your dataset (through the prep-ID) in the [CMS McM website](https://cms-pdmv-prod.web.cern.ch/mcm/)
    - Enable "flownWith" option in the view options 
    - Click on your release and [get setup](https://cms-pdmv-prod.web.cern.ch/mcm/public/restapi/requests/get_setup/PPD-Phase2Spring24pLHEGS-00002) from ```PPD-Phase2Spring24pLHEGS-00002```.
    This setup should work for all processes with the same campaign, expect for the ```GenFragment.py``` which is a configuration file that sets up the event generation process using Pythia8. 
A common version can be reached in this way:
```curl -s -k https://cms-pdmv-prod.web.cern.ch/mcm/public/restapi/requests/get_fragment/PPD-Phase2Spring24pLHEGS-00002 --retry 3 --create-dirs -o Configuration/GenProduction/python/PPD-Phase2Spring24pLHEGS-00002-fragment.py```

    
    The _second_ command runs the GEN-SIM simulation, taking the events from the previous step (```.lhe```).
    ```-- no_exec``` ensures that the ```cmsDriver``` does not execute the command immediately and just generates the configuration file:
    ```cmsDriver.py Configuration/GenProduction/python/PPD-Phase2Spring24pLHEGS-00002-fragment.py 
    --eventcontent FEVTDEBUG 
    --customise Configuration/DataProcessing/Utils.addMonitoring 
    --datatier GEN-SIM 
    --conditions 140X_mcRun4_realistic_v4 
    --beamspot HLLHC14TeV 
    --step GEN,SIM 
    --geometry Extended2026D110 
    --nStreams 2 
    --era Phase2C17I13M9 
    --python_filename PPD-Phase2Spring24pLHEGS-00002_2_cfg.py 
    --fileout file:PPD-Phase2Spring24pLHEGS-00002.root 
    --filein file:PPD-Phase2Spring24pLHEGS-00002_0.lhe
    --no_exec --mc -n $EVENTS || exit $? ;
    ```

    ! In [get setup](https://cms-pdmv-prod.web.cern.ch/mcm/public/restapi/requests/get_setup/PPD-Phase2Spring24pLHEGS-00002), you will find two cmsDriver commands. The first one simply converts the ```.lhe``` file into a ```.root``` file, which is required for the second cmsDriver command. However, you can skip this step by specifying the ```.lhe``` extension in the ```--filein``` parameter of the second cmsDriver command (as shown in the example above).
    
    ! If you want to generate events from scratch, the GenFragment will need to define the physics process explicitly, in addition to configuring the parton showers, hadronization and other simulation settings. Since you are not starting from an LHE file, leave the ```filein``` parameter empty. 
    

- **DIGI-RAW step**: it takes the GEN-SIM file generated from the previous step and applies the digitalization of the simulated events, simulating how the detector would record the signals for each event. To get the ```cmsDriver.py``` command for DIGI-RAW step:

    1. Go back to the [CMS McM link](https://cms-pdmv-prod.web.cern.ch/mcm/) of your dataset
    2. In the ```Actions``` column, there will be a small circle with a downward arrow. This icon lets you access additional commands ([example here](https://cms-pdmv-prod.web.cern.ch/mcm/public/restapi/requests/get_setup/TSG-Phase2Spring24DIGIRECOMiniAOD-00118)). The first one is the command of our interest:
    
        ```
        cmsDriver.py  
        --eventcontent FEVTDEBUGHLT 
        --pileup 'AVE_140_BX_25ns' 
        --customise SLHCUpgradeSimulations/Configuration/aging.customise_aging_1000,SimGeneral/MixingModule/customiseStoredTPConfig.higherPtTP,Configuration/DataProcessing/Utils.addMonitoring 
        --datatier GEN-SIM-DIGI-RAW 
        --conditions 140X_mcRun4_realistic_v4 
        --customise_commands "process.FEVTDEBUGHLToutput.outputCommands.append('keep *_l1tSC8PFL1PuppiCorrectedEmulator_*_HLT')" 
        --step DIGI:pdigi_valid,L1TrackTrigger,L1,DIGI2RAW,HLT:@relval2026 
        --geometry Extended2026D110 
        --nStreams 2 
        --era Phase2C17I13M9 
        --python_filename TSG-Phase2Spring24DIGIRECOMiniAOD-00118_1_cfg.py 
        --fileout file:TSG-Phase2Spring24DIGIRECOMiniAOD-00118_0.root 
        --filein file:TSG-Phase2Spring24GS-00167.root 
        --pileup_input "dbs:/MinBias_TuneCP5_14TeV-pythia8/Phase2Spring24GS-140X_mcRun4_realistic_v4-v1/GEN-SIM" 
        --no_exec --mc -n $EVENTS || exit $? ;
        ```

    ! Remember ```voms-proxy-init -voms cms –rfc``` create a valid authetication proxy to access DAS (for the pileup dataset).

- **FPinputs step**: the dataset slimming step is the first part of the **FastPUPPI** workflow. Its main purpose is to create "slimmed" input files that contain a minimal set of products required for:
    - Re-running the full Correlator task (i.e., input trigger primitive (TP) collections).
    - Performing analysis (i.e., GEN particles, Tracking particles, etc.).
    
    This step extracts only the necessary information from the GEN-SIM-DIGI-RAW dataset, reducing the file size while preserving the essential data. To run it we need a configuration file:
    1. Follow the FastPUPPI [README](https://github.com/p2l1pfp/FastPUPPI/blob/14_2_X/NtupleProducer/README.md).
    2. Use the correct script for the ```Phase2Spring24``` campaign: ```runInputs140X.py``` (```Phase2C17I13M9```, ```Geometry D110```).
    ```140X_v0``` input files from processing ```14_0_X``` ```Phase2Spring24``` samples in ```CMSSW_14_2_0_pre2``` + ```p2l1pfp:l1ct-142x-v1.0``` are available in ```/eos/cms/store/cmst3/group/l1tr/FastPUPPI/14_2_X/fpinputs_140X/v0/```


- **Job Submission**: the next step is to combine all configurations and submit jobs for production. This involves:
    1. setting up the CMSSW environment:
        ```
        export SCRAM_ARCH=el8_amd64_gcc12
        source /cvmfs/cms.cern.ch/cmsset_default.sh

        if [ -r CMSSW_14_0_9/src ] ; then
            echo "Release CMSSW_14_0_9 already exists"
        else
            scram p CMSSW CMSSW_14_0_9
        fi

        cd CMSSW_14_0_9/src
        eval `scram runtime -sh`
        ```

     2. clone the [Submission Repository](https://github.com/cerminar/submission/tree/master): 
        ```
        git clone https://github.com/cerminar/submission.git
        cd submission
        ```

    3. Modify the relevant YAML file: ```submit_GENSIM_DIGIRAW_INFP_140X.yaml```

        ```
        Common:
          mode: 3STEPS   # Defines a 3-step workflow (GEN-SIM → DIGI-RAW → FastPUPPI inputs)
          name: gensim_digiraw_infp  # Job name

          tasks:
            - m20  # Defines a dataset processing task

          version: 142Xv0  # CMSSW version being used for the last step
          output_dir_base: /eos/cms/store/cmst3/group/l1tr/vcamagni/L1TauID/DATA/FPinputs  # Directory where output files will be stored
          ncpu: 4  # Number of CPU cores per job
          max_memory: 7000  # Memory limit (in MB)
          output_file_name: inputs140X.root  # Name of the output ROOT file

        Configuration:
          - mode: FEVTDEBUG
            cmssw_config: ../step1.py
          - mode: FEVTDEBUGHLT
            cmssw_config: ../step2.py
          - mode: INFP
            cmssw_config: /afs/cern.ch/user/v/vcamagni/FPinputs/CMSSW_14_2_0_pre2/src/FastPUPPI/NtupleProducer/python/runInputs140X.py

        m20:
          input_files:
            - file:/eos/cms/store/cmst3/group/l1tr/vcamagni/L1TauID/DATA/LHE/m20/m20.lhe
          crab: False
          splitting_mode: event_ranges
          splitting_granularity: 250
          job_flavor: workday
          max_events: 1000000
        
        ```
         It's purpose is to define overall settings like workflow mode, storage paths, resources (CPU/memory), and output file names. 
         The three CMSSW steps that will run in sequence are defined in the ```Configuration```:
         - **FEVTDEBUG** (step1.py) → First step (GEN-SIM) generated from the cmsDriver command for the GEN-SIM step.
         - **FEVTDEBUGHLT** (step2.py) → Second step (DIGI-RAW) generated from the cmsDriver command for the DIGI-RAW step.
         - **INFP** (runInputs140X.py) → Third step (FastPUPPI input slimming)
        
        
        The last part is about _Task-Specific Settings (Dataset m20)_. It uses an LHE input file (```m20.lhe```) which comes from the first first LHE Generation step.
        Splitting is done in event ranges of 250 events per job.
        Uses Condor’s "workday" queue (suitable for jobs running <8 hours).
        Runs up to 1 million events (number of events generated in the LHE step).
        
        ! If you don't start from an ```.lhe``` file but directly from the GenFragment, leave the ```input_files: -``` field empty and comment ```process.source.fileNames = cms.untracked.vstring(TEMPL_INFILES)``` in the ```templates/jobCustomization_FEVTDEBUG_cfg.py```.
        
        The ```[Common['mode']]``` will recall the ```run_3STEPS.sh``` script which automates the process of running the three sequential CMSSW steps. It:

        - loads environment variables and configurations from ```params.sh```;
        - sets up the CMSSW environment for the required version (```CMSSWVERSION```) and architecture (```scramarch```);
        - runs _step1_ using ```cmsRun``` command and the ```job_config_step1_${PROCID}.py``` configuration file (the output is saved into a compressed log file:```step1_${PROCID}.${CLUSTERID}.log.gz```)
        - runs _step2_ using ```cmsRun``` command and the ```job_config_step2_${PROCID}.py``` configuration file (the output is saved into a compressed log file:```step2_${PROCID}.${CLUSTERID}.log.gz```)
        - switches to the specific CMSSW version for FastPuppi input slimming step: ```CMSSW_14_2_pre2```
        
            ```
            echo 'Switching to CMSSW_14_2_0_pre2 for STEP3...'
            source /cvmfs/cms.cern.ch/cmsset_default.sh
            cd /afs/cern.ch/user/v/vcamagni/FPinputs/CMSSW_14_2_0_pre2
            eval `scram runtime -sh`
            ```
            ! Specify here the path to your FP release.
        
        Commands:
        Inline help: ```python3 submit.py --help```
        Create the job configuration: ```python3 submit.py -f submit.yaml --create```
        Submit the jobs to the queues: ```python submit.py -f submit.yaml --submit```




    

    




