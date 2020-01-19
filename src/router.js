import Vue from 'vue'
import Router from 'vue-router'
import Observations from './views/Observations.vue'
import Sources from './views/Sources.vue'

Vue.use(Router)

export default new Router({
  mode: 'history',
  base: process.env.BASE_URL,
  routes: [
    {
      path: '/observations',
      name: 'observations',
      component: Observations
    },
    {
      path: '/stars',
      name: 'stars',
      component: Sources
    },
    {
      path: '/observations/:sequenceId',
      name: 'observationDetail',
      // route level code-splitting
      // this generates a separate chunk (about.[hash].js) for this route
      // which is lazy-loaded when the route is visited.
      component: () => import(/* webpackChunkName: "about" */ './views/ObservationDetail.vue')
    },
    {
      path: '/stars/:picid',
      name: 'sourceDetail',
      // route level code-splitting
      // this generates a separate chunk (about.[hash].js) for this route
      // which is lazy-loaded when the route is visited.
      component: () => import(/* webpackChunkName: "about" */ './views/SourceDetail.vue')
    }
    // { path: '*', redirect: 'home' }
  ]
})
