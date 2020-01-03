import Vue from 'vue'
import Vuex from 'vuex'

import { SourcesService } from './services/SourcesService.js'

const request = require('request');

let sources = new SourcesService();

Vue.use(Vuex)



export default new Vuex.Store({
  state: {
      picid: null,
      frameIndex: 0,
      totalFrames: null,
      sources: sources,
      observations: [],
      sourceRecord: null,
      sourceRunDetail: null,
      piaaRecord: null,
      locationData: {},
      stampData: {},
      lightcurveData: {},
      rawData: {},
      pixelData: {}
  },
  mutations: {
      setSource(state, picid) {
        state.picid = picid;
        // Reset everything.
        state.observations = [];
        state.sourceRecord = null;
        state.sourceRunDetail = null;
        state.piaaRecord = null;
        state.locationData = {};
        state.stampData = {};
        state.lightcurveData = {};
        state.rawData = {};
        state.plotData = {};
        state.frameIndex = 0;
        state.totalFrames = null;
      },
      setFrame(state, record) {
        state.frameIndex = record;
        if (state.frameIndex == state.totalFrames){
          state.frameIndex = 0;
        }
        if (state.frameIndex == -1){
          state.frameIndex = state.totalFrames - 1;
        }
      },
      setFrameSize(state, record) { state.totalFrames = record },
      setSourceRecord(state, record) { state.sourceRecord = record },
      setRunDetail(state, record){ state.sourceRunDetail = record },
      setPiaaRecord(state, record){ state.piaaRecord = record },
      setLocationData(state, record){ state.locationData = record },
      setStampData(state, record){ state.stampData = record },
      setLightcurveData(state, record){ state.lightcurveData = record },
      setPixelData(state, record){ state.pixelData = record },
      setRawCounts(state, record){ state.rawData = record },
      setObservations(state, records){ state.observations = records },
      addObservationRun(state, data) { state.observations.push(data) }
  },
  actions: {
      setFrame({ commit, state }, newIndex ){ commit('setFrame', newIndex) },
      setSource({ commit, state }, picid) {
        // Set property
        commit('setSource', picid);

        // Get all the observation proessing runs for source.
        state.sources.getSourceObservations(state.picid).then((response) => {
          if (response.status == 200){
            commit('setObservations', response.data.piaa_runs);
          }
        })
        .catch((err) => {
          console.log('Error getting observation runs', err);
        });

        state.sources.getSource(state.picid).then((response) => {
          if (response.status == 200){
            commit('setSourceRecord', response.data.picid_document);
          }
        })
        .catch((err) => {
          console.log('Error getting documents', err);
        });
      },

      selectRow: function({ commit, state, dispatch }, row) {
        commit('setRunDetail', row);

        commit('setPiaaRecord', {});
        state.sources.getPIAA(state.picid, row.id)
        .then((response) => {
          if (response.status == 200){
            commit('setPiaaRecord', response.data.piaa_document);
          }
        })
        .catch((err) => { console.log('Error getting PIAA details', err); });

        dispatch('getLightcurve');
        dispatch('getRawCounts');
        dispatch('getReferenceLocations');
        dispatch('getPixelDrift');
        dispatch('getPSC');
      },

      getLightcurve: function({ commit, state }) {
        commit('setLightcurveData', {})
        state.sources.getLightcurveData(state.picid, state.sourceRunDetail.id).then((response) => {
          if (response.status == 200){
            commit('setLightcurveData', response.data.lightcurve)
          }
        }).catch(function(error){
          console.log(error)
        });
      },

      getPSC: function({ commit, state }) {
        commit('setStampData', {})
        state.sources.getPSC(state.picid, state.sourceRunDetail.id).then((response) => {
          if (response.status == 200){
            commit('setStampData', response.data.psc)
            commit('setFrameSize', response.data.psc.target.length)
          }
        }).catch(function(error){
          console.log(error)
        });
      },

      getRawCounts: function({ commit, state }) {
        commit('setRawCounts', {})
        state.sources.getRawCounts(state.picid, state.sourceRunDetail.id).then((response) => {
          if (response.status == 200){
            commit('setRawCounts', response.data.counts)
          }
        });
      },

      getPixelDrift: function({ commit, state }) {
        commit('setPixelData', {});
        state.sources.getPixelDrift(state.picid, state.sourceRunDetail.id).then((response) => {
          if (response.status == 200){
            commit('setPixelData', response.data.pixel_drift);
          }
        });
      },

      getReferenceLocations: function({ commit, state }) {
        commit('setLocationData', {})
        state.sources.getReferenceLocations(state.picid, state.sourceRunDetail.id).then((response) => {
          if (response.status == 200){
            commit('setLocationData', response.data.ref_locations)
          }
        });
      }
  }
})
