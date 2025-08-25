import { createSlice } from '@reduxjs/toolkit';

     const authSlice = createSlice({
       name: 'auth',
       initialState: { user: null, token: null },
       reducers: {
         setUser: (state, action) => {
           state.user = action.payload;
           state.token = action.payload.access_token;
         },
       },
     });

     export const { setUser } = authSlice.actions;
     export default authSlice.reducer;