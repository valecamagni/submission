import FWCore.ParameterSet.Config as cms

from TEMPL_ROOTCFG import process

process.maxEvents.input = cms.untracked.int32(TEMPL_NEVENTS)
process.source.fileNames = cms.untracked.vstring(TEMPL_INFILES)

if process.source.type_() != 'EmptySource':
    process.source.skipEvents = cms.untracked.uint32(TEMPL_SKIPENVETS)

#Setup FWK for multithreaded
process.options.numberOfThreads=cms.untracked.uint32(TEMPL_NCPU)
process.options.numberOfStreams=cms.untracked.uint32(0)
process.options.numberOfConcurrentLuminosityBlocks=cms.untracked.uint32(1)
process.LHEoutput.fileName = cms.untracked.string('TEMPL_OUTFILE')
