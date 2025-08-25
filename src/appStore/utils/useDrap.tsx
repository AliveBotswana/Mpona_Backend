import React, { MouseEventHandler } from 'react';

     function useDrap<T extends HTMLElement>(
       ref: React.MutableRefObject<T>
     ): MouseEventHandler<T> {
       return () => {};
     }

     export default useDrap;