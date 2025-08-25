import { Role } from './Role';

      export default interface User {
        id: number;
        username: string;
        password: string;
        roles: Role[];
      }