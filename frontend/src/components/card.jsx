import React from 'react'
import { Box, Card } from "@radix-ui/themes";

const CardComponent = ({ src, onClick }) => {
  return (
    <div onClick={onClick} className='cursor-pointer'>
        <Box maxWidth="240px">
            <Card>
               <img src={src} alt="item" width="200" height="600" />
            </Card>
        </Box>
    </div>
  )
}

export default CardComponent