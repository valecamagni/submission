import FWCore.ParameterSet.Config as cms

from TEMPL_ROOTCFG import process


process.source.fileNames = cms.untracked.vstring(TEMPL_INFILES)
## Events and lumi blocks
process.maxEvents.input = cms.untracked.int32(TEMPL_NEVENTS)
if process.source.type_() != 'EmptySource':
    process.source.skipEvents = cms.untracked.uint32(TEMPL_SKIPENVETS)
process.source.firstLuminosityBlock = cms.untracked.uint32(TEMPL_FIRSTLUMI)
## Scramble
import random
# rnd = random.SystemRandom()
for X in process.RandomNumberGeneratorService.parameterNames_(): 
   if X != 'saveFileName': getattr(process.RandomNumberGeneratorService,X).initialSeed = cms.untracked.uint32(TEMPL_SEED)
 
#process.RAWSIMoutput.fileName = cms.untracked.string('file:TEMPL_OUTFILE')
process.FEVTDEBUGoutput.fileName = cms.untracked.string('file:TEMPL_OUTFILE')

#Setup FWK for multithreaded
process.options.numberOfThreads=cms.untracked.uint32(TEMPL_NCPU)
process.options.numberOfStreams=cms.untracked.uint32(0)
process.options.numberOfConcurrentLuminosityBlocks=cms.untracked.uint32(1)
process.options.wantSummary = cms.untracked.bool(True)
