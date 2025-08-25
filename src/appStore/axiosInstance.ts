import axios from 'axios';

     const AXIOS_CLIENT = axios.create({
       baseURL: 'http://localhost:7071',
     });

     export { AXIOS_CLIENT };
     export const baseURL = 'http://localhost:7071';