import { request } from '@/utils'

export default {
  login: (data) => request.post('/base/access_token', data, { noNeedToken: true }),
  register: (data) => request.post('/base/register', data, { noNeedToken: true }),
  getUserInfo: () => request.get('/base/userinfo'),
  getUserMenu: () => request.get('/base/usermenu'),
  getUserApi: () => request.get('/base/userapi'),
  // profile
  updatePassword: (data = {}) => request.post('/base/update_password', data),
  updateAvatar: (formData) => request.post('/base/update_avatar', formData),
  // users
  getUserList: (params = {}) => request.get('/user/list', { params }),
  getUserById: (params = {}) => request.get('/user/get', { params }),
  createUser: (data = {}) => request.post('/user/create', data),
  updateUser: (data = {}) => request.post('/user/update', data),
  deleteUser: (params = {}) => request.delete(`/user/delete`, { params }),
  resetPassword: (data = {}) => request.post(`/user/reset_password`, data),
  // role
  getRoleList: (params = {}) => request.get('/role/list', { params }),
  createRole: (data = {}) => request.post('/role/create', data),
  updateRole: (data = {}) => request.post('/role/update', data),
  deleteRole: (params = {}) => request.delete('/role/delete', { params }),
  updateRoleAuthorized: (data = {}) => request.post('/role/authorized', data),
  getRoleAuthorized: (params = {}) => request.get('/role/authorized', { params }),
  // menus
  getMenus: (params = {}) => request.get('/menu/list', { params }),
  createMenu: (data = {}) => request.post('/menu/create', data),
  updateMenu: (data = {}) => request.post('/menu/update', data),
  deleteMenu: (params = {}) => request.delete('/menu/delete', { params }),
  // apis
  getApis: (params = {}) => request.get('/api/list', { params }),
  createApi: (data = {}) => request.post('/api/create', data),
  updateApi: (data = {}) => request.post('/api/update', data),
  deleteApi: (params = {}) => request.delete('/api/delete', { params }),
  refreshApi: (data = {}) => request.post('/api/refresh', data),
  // depts
  getDepts: (params = {}) => request.get('/dept/list', { params }),
  createDept: (data = {}) => request.post('/dept/create', data),
  updateDept: (data = {}) => request.post('/dept/update', data),
  deleteDept: (params = {}) => request.delete('/dept/delete', { params }),
  // auditlog
  getAuditLogList: (params = {}) => request.get('/auditlog/list', { params }),
  // food
  recognizeFood: (data) => request.post('/food/recognize', data),
  getFoodHistory: (params = {}) => request.get('/food/history', { params }),
  getFoodRecordDetail: (id) => request.get(`/food/record/${id}`),
  deleteFoodRecord: (id) => request.delete(`/food/record/${id}`),
  batchDeleteFoodRecords: (ids) => request.delete('/food/records/batch', { data: { record_ids: ids } }),
  // food management
  getFoodCategories: (params = {}) => request.get('/food/categories', { params }),
  getFoodCategoryDetail: (id) => request.get(`/food/categories/${id}`),
  createFoodCategory: (data) => request.post('/food/categories', data),
  updateFoodCategory: (id, data) => request.put(`/food/categories/${id}`, data),
  deleteFoodCategory: (id) => request.delete(`/food/categories/${id}`),
  createFoodCategoryWithUpload: (formData) => request.post('/food/categories/upload', formData),
  updateFoodCategoryWithUpload: (id, formData) => request.put(`/food/categories/${id}/upload`, formData),
  updateNutritionInfo: (foodId, data) => request.put(`/food/nutrition/${foodId}`, data),
}
