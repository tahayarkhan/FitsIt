import React from 'react'
import { Box, Card } from "@radix-ui/themes";

const CardComponent = ({ src }) => {
  return (
    <div>
        <Box maxWidth="240px">
            <Card>
               <img src={src} alt="item" width="200" height="600" />
            </Card>
        </Box>
    </div>
  )
}

export default CardComponent